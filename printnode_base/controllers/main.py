# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

import json
import werkzeug
import base64
import logging

from copy import deepcopy

from odoo.addons.web.controllers.main import DataSet, ReportController

from odoo.http import request, serialize_exception as _serialize_exception
from odoo.tools.translate import _
from odoo import http, api

from werkzeug.urls import url_unquote

_logger = logging.getLogger(__name__)

SECURITY_GROUP = 'printnode_base.printnode_security_group_user'
SUPPORTED_REPORT_TYPES = [
    'qweb-pdf',
    'qweb-text',
    'py3o',
]


class DataSetProxy(DataSet):

    def _execute_printnode_jobs(self, action_ids, action_object_ids):
        for action in request.env['printnode.action.button'].browse(action_ids):
            objects = action._get_model_objects(action_object_ids)
            if not objects:
                continue
            printer, printer_bin = action._get_action_printer()
            options = {'bin': printer_bin.name} if printer_bin else {}
            printer.printnode_print(
                action.report_id,
                objects,
                copies=action.number_of_copies,
                options=options,
            )

    def _call_kw(self, model, method, args, kwargs):
        user = request.env.user
        if not user.has_group(SECURITY_GROUP) \
                or not request.env.company.printnode_enabled or not user.printnode_enabled:
            return super(DataSetProxy, self)._call_kw(model, method, args, kwargs)

        # We have a list of methods which will never be handled in 'printnode.action.button'.
        # In that case just will be returned a 'super method'.
        su = request.env['ir.config_parameter'].sudo()
        methods_list = su.get_param('printnode_base.skip_methods', '').split(',')
        # In addition, we need to choose only 'call_kw_multi' sub method, so
        # let's filter this like in standard Odoo function 'def call_kw()'.
        method_ = getattr(type(request.env[model]), method)
        api_ = getattr(method, '_api', None)
        if (method in methods_list) or (api_ in ('model', 'model_create')):
            return super(DataSetProxy, self)._call_kw(model, method, args, kwargs)

        actions = request.env['printnode.action.button'].sudo().search([
            ('model_id.model', '=', model),
            ('method_id.method', '=', method),
        ])
        post_ids, pre_ids = [], []

        for action in actions.filtered(lambda a: a.active and a.report_id):
            (post_ids, pre_ids)[action.preprint].append(action.id)

        printnode_object_ids = args[0] if args else None

        self._execute_printnode_jobs(pre_ids, printnode_object_ids)

        # We need to update variables 'post_ids' and 'printnode_object_id' from context.
        args_, kwargs_ = deepcopy(args[1:]), deepcopy(kwargs)
        context_, *_rest = api.split_context(method_, args_, kwargs_)
        if isinstance(context_, dict):
            post_ids += context_.get('printnode_action_ids', [])
            object_ids_from_kwargs = context_.get('printnode_object_ids')
            printnode_object_ids = object_ids_from_kwargs or printnode_object_ids

        result = super(DataSetProxy, self)._call_kw(model, method, args, kwargs)

        # If we had gotten 'result' as another one wizard or something - we need to save our
        # variables 'printnode_action_ids' and 'printnode_object_ids' in context and do printing
        # after the required 'super method' will be performed.
        if post_ids and result and isinstance(result, dict) and 'context' in result:
            new_context = dict(result.get('context'))
            if not new_context.get('printnode_action_ids'):
                new_context.update({'printnode_action_ids': post_ids})
            if not new_context.get('printnode_object_ids'):
                new_context.update({'printnode_object_ids': printnode_object_ids})
            result['context'] = new_context
            return result

        if not post_ids:
            return result

        self._execute_printnode_jobs(post_ids, printnode_object_ids)

        return result


class ReportControllerProxy(ReportController):

    def _check_direct_print(self, data):
        print_data = {'can_print': False}
        request_content = json.loads(data)

        report_url, report_type, printer_id, printer_bin = \
            request_content[0], request_content[1], request_content[2], request_content[3]

        # Get workstation devices from request (if specified)
        # Moved to separate block for backward compatibility with old versions
        workstation_devices = {}
        if len(request_content) > 4:
            workstation_devices = request_content[4]

        print_data['report_type'] = report_type

        if printer_id:
            printer_id = request.env['printnode.printer'].browse(printer_id)
        if printer_bin:
            printer_bin = request.env['printnode.printer.bin'].browse(printer_bin)

        # Add workstations devices to context (if presented)
        new_context = request.env.context.copy()
        workstation_devices = {k: v for k, v in workstation_devices.items() if v is not None}

        if workstation_devices:
            new_context.update(workstation_devices)

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
        report_name = report_url.split('/report/{}/'.format(extension))[1].split('?')[0]

        if '/' in report_name:
            report_name, ids = report_name.split('/')

            if ids:
                ids = [int(x) for x in ids.split(",")]
                print_data['ids'] = ids

        report = request.env['ir.actions.report']._get_report_from_name(report_name)
        model = request.env[report.model_id.model]

        print_data['model'] = model

        rp = request.env['printnode.report.policy'].search([
            ('report_id', '=', report.id),
        ])
        if rp and rp.exclude_from_auto_printing:
            # If report is excluded from printing, than just download it
            return print_data

        print_data["report_policy"] = rp

        # STEP 4. Now let's check if we can define printer for the current report.
        # If not - just reset to default
        if not printer_id:
            printer_id, printer_bin = user.with_context(new_context).get_report_printer(report.id)

        if not printer_id:
            return print_data

        print_data["printer_id"] = printer_id
        print_data["printer_bin"] = printer_bin
        print_data["can_print"] = True

        return print_data

    @http.route('/report/check', type='http', auth="user")
    def report_check(self, data, context=None):
        print_data = self._check_direct_print(data)
        if print_data['can_print']:
            return "true"
        return "false"

    @http.route('/report/print', type='http', auth="user")
    def report_print(self, data, context=None):

        print_data = self._check_direct_print(data)
        if not print_data['can_print']:
            return json.dumps({
                'title': _('Printing not allowed!'),
                'message': _('Please check your DirectPrint settings or close and open app again'),
                'success': False,
                'notify': True,
            })

        rp = print_data['report_policy']
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
                'size': rp and rp.report_paper_id,
                'options': {'bin': printer_bin.name} if printer_bin else {},
            }
            res = printer_id.printnode_print_b64(ascii_data, params)

            if res:
                self._postprint_actions(print_data['model'], print_data.get('ids', []))
        except Exception as e:
            _logger.exception(e)
            se = _serialize_exception(e)
            error = {
                'success': False,
                'code': 200,
                'message': "Odoo Server Error",
                'data': se
            }
            return json.dumps(error)

        title = _('Report was sent to printer')
        message = _('Document "%s" was sent to printer %s') % (report_name, printer_id.name)
        return json.dumps({
            'title': title,
            'message': message,
            'success': True,
            'notify': request.env.company.im_a_teapot
        })

    @http.route('/dpc/release-model-check', type='http', auth="user")
    def release_model_check(self, context=None):
        model = request.env['ir.model'].sudo().search([['model', '=', 'printnode.release']])
        if model:
            return "true"
        return "false"

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
        if 'api_key' not in kwargs:
            return _('No API Key returned. Please, copy the key and paste in the module settings')

        request.env['printnode.account'].update_main_account(kwargs['api_key'])

        settings_action_id = request.env.ref('printnode_base.printnode_config_action').id
        return werkzeug.utils.redirect(
            '/web?view_type=form&model=res.config.settings#action={}'.format(settings_action_id)
        )
