# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

import base64
import hashlib
import hmac
import json
import logging
import werkzeug

from copy import deepcopy
from datetime import datetime

from odoo import http, api
from odoo.addons.web.controllers.report import ReportController
from odoo.addons.web.controllers.dataset import DataSet
from odoo.http import request, db_list, serialize_exception
from odoo.tools.translate import _

from werkzeug.exceptions import BadRequest, NotFound, SecurityError
from werkzeug.urls import url_unquote

from .utils import add_env


_logger = logging.getLogger(__name__)

SECURITY_GROUP = 'printnode_base.printnode_security_group_user'
SUPPORTED_REPORT_TYPES = [
    'qweb-pdf',
    'qweb-text',
    'qweb-py3o',
]


class DataSetProxy(DataSet):

    def _call_kw(self, model, method, args, kwargs):
        """ Overriding the default method to add custom logic with action buttons, etc.
        """
        # We have to skip this method due to an issue with this method
        # (action_replenish uses filter by date and will break if transaction will be opened earlier
        # than value in variable "now"). Check ticket VENSUP-3536 for more details
        if method == 'action_replenish':
            return super(DataSetProxy, self)._call_kw(model, method, args, kwargs)

        user = request.env.user
        if not user.has_group(SECURITY_GROUP) \
                or not request.env.company.printnode_enabled or not user.printnode_enabled:
            return super(DataSetProxy, self)._call_kw(model, method, args, kwargs)

        # We have a list of methods which will never be handled in 'printnode.action.button'.
        # In that case just will be returned a 'super method'.
        methods_list = request.env['ir.config_parameter'].sudo() \
            .get_param('printnode_base.skip_methods', '').split(',')
        # In addition, we need to choose only 'call_kw_multi' sub method, so
        # let's filter this like in standard Odoo function 'def call_kw()'.
        method_ = getattr(type(request.env[model]), method)
        api_ = getattr(method, '_api', None)
        if (method in methods_list) or (api_ in ('model', 'model_create')):
            return super(DataSetProxy, self)._call_kw(model, method, args, kwargs)

        # Get context parameters with keys starting with 'printnode_' (workstation devices)
        printnode_context = dict(filter(
            lambda i: i[0].startswith('printnode_'), kwargs.get('context', {}).items()
        ))

        ActionButton = request.env['printnode.action.button']
        post_action_ids, pre_action_ids = \
            ActionButton._get_post_pre_action_button_ids(model, method)

        report_object_ids = args[0] if args else None

        ActionButton.browse(pre_action_ids).with_context(**printnode_context).\
            print_reports(report_object_ids)

        # We need to update variables 'post_action_ids' and 'printnode_object_id' from context.
        args_, kwargs_ = deepcopy(args[1:]), deepcopy(kwargs)
        context_, *_rest = api.split_context(method_, args_, kwargs_)
        if isinstance(context_, dict):
            post_action_ids += context_.get('printnode_action_ids', [])
            object_ids_from_kwargs = context_.get('report_object_ids')
            report_object_ids = object_ids_from_kwargs or report_object_ids

        result = super(DataSetProxy, self)._call_kw(model, method, args, kwargs)

        # If we had gotten 'result' as another one wizard or something - we need to save our
        # variables 'printnode_action_ids' and 'report_object_ids' in context and do printing
        # after the required 'super method' will be performed.
        if post_action_ids and result and isinstance(result, dict) and 'context' in result:
            new_context = dict(result.get('context'))
            if not new_context.get('printnode_action_ids'):
                new_context.update({'printnode_action_ids': post_action_ids})
            if not new_context.get('report_object_ids'):
                new_context.update({'report_object_ids': report_object_ids})
            result['context'] = new_context
            return result

        if not post_action_ids:
            return result

        ActionButton.browse(post_action_ids).with_context(**printnode_context).\
            print_reports(report_object_ids)

        return result


class ReportControllerProxy(ReportController):

    def _check_direct_print(self, data, context):
        """
        This method performs multi-step data validation before sending a print job.

        :param data: a list of params such as report_url, report_type, printer_id, printer_bin
        :param context: current context

        The method returns a dictionary print_data that contains information about the print job.
        The dictionary will have the key can_print set to True if the print job can be sent to
        the printer, and False otherwise.

        The method performs the following steps:
        - Check if direct printing is enabled for the user.
        - Check if the requested report type is supported.
        - Check if the current report is excluded from auto-printing.
        - Check if a printer has been defined for the current report.

        If all checks are passed, set can_print to True and return print_data.
        """
        print_data = {'can_print': False}
        request_content = json.loads(data)

        report_url, report_type, printer_id, printer_bin = \
            request_content[0], request_content[1], request_content[2], request_content[3]

        print_data['report_type'] = report_type

        if printer_id:
            printer_id = request.env['printnode.printer'].browse(printer_id)
        if printer_bin:
            printer_bin = request.env['printnode.printer.bin'].browse(printer_bin)

        # STEP 1: First check if direct printing is enabled for user at all.
        # If no - not need to go further
        user = request.env.user
        if not user.has_group(SECURITY_GROUP) \
                or not request.env.company.printnode_enabled \
                or (not user.printnode_enabled and not printer_id):
            return print_data

        # STEP 2: If we are requesting not PDF or Text file, than also return
        # to standard Odoo behavior.
        if report_type not in SUPPORTED_REPORT_TYPES:
            return print_data

        # STEP 3: Check if current reports is excluded from the Auto Printing.
        # If yes, call standard Odoo functionality
        extension = report_type
        if '-' in report_type:
            extension = report_type.split('-')[1]
        report_name = report_url.split(f'/report/{extension}/')[1].split('?')[0]

        if '/' in report_name:
            report_name, ids = report_name.split('/')

            if ids:
                ids = [int(x) for x in ids.split(",") if x.isdigit()]
                print_data['ids'] = ids

        report = request.env['ir.actions.report']._get_report_from_name(report_name)
        model = request.env[report.model_id.model]

        print_data['model'] = model

        report_policy = request.env['printnode.report.policy'].search([
            ('report_id', '=', report.id),
        ])
        if report_policy and report_policy.exclude_from_auto_printing:
            # If report is excluded from printing, than just download it
            return print_data

        print_data["report_policy"] = report_policy

        # STEP 4. Now let's check if we can define printer for the current report.
        # If not - just reset to default
        if not printer_id:
            # Update context (there can be information about workstation devices)
            new_context = dict(request.env.context)
            context = json.loads(context or '{}')
            new_context.update(context)

            printer_id, printer_bin = user.with_context(**new_context).get_report_printer(report.id)

        if not printer_id:
            return print_data

        print_data["printer_id"] = printer_id
        print_data["printer_bin"] = printer_bin
        print_data["can_print"] = True

        return print_data

    @http.route('/report/check', type='http', auth="user")
    def report_check(self, data, context=None):
        print_data = self._check_direct_print(data, context)
        if print_data['can_print']:
            return "true"
        return "false"

    @http.route('/report/print', type='http', auth="user")
    def report_print(self, data, context=None):
        """
        Handles sending a report to a printer.

        :param data: The data to be printed.
        :param context optional: dict with current context.
        :return: a JSON-encoded response with info about the success or failure of the print job.

        It calls the _check_direct_print method, which performs several checks to validate whether
        the report can be printed directly.
        If direct printing is not allowed (according to the results of the _check_direct_print
        method), the method returns a JSON response indicating that printing is not allowed.

        If direct printing is allowed, the method proceeds to download the report using
        the report_download method.

        The downloaded report is then sent to the printer using the printnode_print_b64 method.
        This method takes the report data in Base64-encoded format, as well as other parameters
        like the printer ID, the report type, and the paper size.

        If the report is successfully sent to the printer, the method performs some post-printing
        actions. If an error occurs during printing, the method returns a JSON response with details
        about the error.

        Finally, the method returns a JSON response indicating whether the printing was successful,
        along with a message to the user indicating the name of the report and the printer to which
        it was sent.
        """
        print_data = self._check_direct_print(data, context)
        if not print_data['can_print']:
            return json.dumps({
                'title': _('Printing not allowed!'),
                'message': _('Please check your DirectPrint settings or close and open app again'),
                'success': False,
                'notify': True,
            })

        report_policy = print_data['report_policy']
        printer_bin = print_data['printer_bin']
        printer_id = print_data['printer_id']

        # Finally if we reached this place - we can send report to printer.
        standard_response = self.report_download(data, context)

        # If we do not have Content-Disposition headed, than no file-name
        # was generated (maybe error)
        content_disposition = standard_response.headers.get('Content-Disposition')
        if not content_disposition:
            return standard_response

        report_name = content_disposition.split("attachment; filename*=UTF-8''")[1]
        report_name = url_unquote(report_name)
        ascii_data = base64.b64encode(standard_response.data).decode('ascii')

        try:
            params = {
                'title': report_name,
                'type': print_data['report_type'],
                'size': report_policy and report_policy.report_paper_id,
                'options': {'bin': printer_bin.name} if printer_bin else {},
            }
            res = printer_id.printnode_print_b64(ascii_data, params)

            if res:
                self._postprint_actions(print_data['model'], print_data.get('ids', []))
        except Exception as exc:
            _logger.exception(exc)
            error = {
                'success': False,
                'code': 200,
                'message': "Odoo Server Error",
                'data': serialize_exception(exc)
            }
            return json.dumps(error)

        title = _('Report was sent to printer')
        message = _(
            'Document "%(report)s" was sent to printer %(printer)s',
            report=report_name,
            printer=printer_id.name,
        )
        return json.dumps({
            'title': title,
            'message': message,
            'success': True,
            'notify': request.env.company.im_a_teapot
        })

    def _postprint_actions(self, model, ids):
        """
        Different post print actions.
        For now it do:
            - Update printnode_printed flag for all printed records (if flag exists)
        """
        if (
            ids
            and 'printnode_printed' in model._fields
            and not model._fields['printnode_printed'].inherited
        ):
            model.browse(ids).write({
                'printnode_printed': True,
            })


class DPCCallbackController(http.Controller):
    @http.route('/dpc-callback', type='http', auth='user')
    def callback(self, **kwargs):
        """
        Callback method to update main account with current api_key.

        When the user following the link in the wizard gets to "print.ventor.tech" and registers
        there, he gets an API key, after that he will be redirected back to Oduu to this controller.
        This method will first update the API key for the current account, and then redirect the
        user to the settings page.
        """
        if 'api_key' not in kwargs:
            return _('No API Key returned. Please, copy the key and paste in the module settings')

        request.env['printnode.account'].update_main_account(kwargs['api_key'])

        settings_action_id = request.env.ref('printnode_base.printnode_config_action').id
        return werkzeug.utils.redirect(
            f'/web?view_type=form&model=res.config.settings#action={settings_action_id}'
        )


class DPCJobContentController(http.Controller):
    @http.route(
        '/dpc/<string:db>/printjob/<int:job_id>/content',
        type='http', methods=['GET'], auth='none', csrf=False)
    @add_env
    def get_printjob_content(self, db=None, job_id=None, **kw):
        """
        Get the content of a print job by ID.

        :param db: The name of the database where the print job is located.
        :param job_id: The ID of the print job to retrieve the content of.
        :return: The response object containing the print job content.
        """
        signature = request.params.get('signature')
        expiration_timestamp = request.params.get('expires')

        # Request validation
        self._validate_request(db, job_id, signature, expiration_timestamp)

        # Make response
        content, headers = self._handle_printjob_content(job_id)
        response = request.make_response(content, headers)
        return response

    def _validate_request(self, db=None, job_id=None, signature=None, expiration_timestamp=None):
        """
        Validate the parameters of the request.

        :param db: The name of the database where the print job is located.
        :param job_id: The ID of the print job to retrieve the content of.
        :param signature: The signature of the request.
        :param expiration_timestamp: The expiration timestamp of the request.
        :return: True if the request is valid otherwise raise an exception.
        """
        if not job_id:
            raise BadRequest("Printjob ID is required")

        if not expiration_timestamp or not signature:
            raise BadRequest("The URL has expired or is unsigned")

        # Validate database
        if not db:
            raise BadRequest("Database name is required")

        if db not in db_list():
            raise NotFound('Database not found')

        # Validate expiration
        if datetime.utcnow() > datetime.fromtimestamp(int(expiration_timestamp)):
            raise SecurityError('URL has expired')

        # Validate signature
        secret_key = request.env['ir.config_parameter'].sudo().get_param('database.secret')

        validated_signature = hmac.new(
            secret_key.encode('UTF-8'),
            f'{job_id}{expiration_timestamp}'.encode('UTF-8'),
            hashlib.sha256
        ).hexdigest()

        if validated_signature != signature:
            raise SecurityError('Signature is invalid')

        return True

    def _handle_printjob_content(self, job_id):
        """
        Retrieves the content of a print job given its ID and generates response headers.

        :param db: The name of the database where the print job is located.
        :param job_id: The ID of the print job to retrieve the content of.
        :return: A tuple <content, headers>.
        """
        printjob_id = request.env['printnode.printjob'].sudo().search([('id', '=', int(job_id))])

        if not printjob_id:
            raise NotFound("Printjob not found")

        if not printjob_id.attachment_id:
            raise BadRequest("Printjob has no content")

        content_type = printjob_id.attachment_id.mimetype

        if content_type not in ('text/plain', 'application/pdf'):
            raise BadRequest("Printjob has an invalid content type")

        content = base64.b64decode(printjob_id.attachment_id.datas)
        headers = [('Content-Type', content_type), ('Content-Length', len(content))]

        return content, headers
