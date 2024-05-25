# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

import base64
import hashlib
import hmac
import logging
import psycopg2
import requests

from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlencode

from odoo import api, fields, models, registry, SUPERUSER_ID, _
from odoo.exceptions import UserError

from .constants import Constants

_logger = logging.getLogger(__name__)


REQUIRED_REPORT_KEYS = ['title', 'type', 'size']


class PrintNodePrinter(models.Model):
    """ PrintNode Printer entity
    """
    _name = 'printnode.printer'
    _inherit = 'printnode.logger.mixin'
    _description = 'PrintNode Printer'

    printnode_id = fields.Integer('Direct Print ID')

    active = fields.Boolean(
        'Active',
        default=True
    )

    online = fields.Boolean(
        string='Online',
        compute='_compute_printer_status',
        store=True,
        readonly=True
    )

    name = fields.Char(
        'Name',
        size=64,
        required=True
    )

    status = fields.Char(
        'PrintNode Status',
        size=64
    )

    printjob_ids = fields.One2many(
        'printnode.printjob', 'printer_id',
        string='Print Jobs'
    )

    paper_ids = fields.Many2many(
        'printnode.paper',
        string='Papers'
    )

    format_ids = fields.Many2many(
        'printnode.format',
        string='Formats'
    )

    computer_id = fields.Many2one(
        'printnode.computer',
        string='Computer',
        ondelete='cascade',
        required=True,
    )

    printer_bin_ids = fields.One2many(
        'printnode.printer.bin', 'printer_id',
        string='Printer Bins',
        readonly=True,
    )

    default_printer_bin = fields.Many2one(
        'printnode.printer.bin',
        string='Default Bin',
        required=False,
    )

    account_id = fields.Many2one(
        'printnode.account',
        string='Account',
        readonly=True,
        related='computer_id.account_id',
        ondelete='cascade',
    )

    error = fields.Boolean(
        compute='_compute_print_rules',
    )

    notes = fields.Html(
        string='Note',
        compute='_compute_print_rules',
    )

    _sql_constraints = [
        (
            'printnode_id',
            'unique(printnode_id)',
            'Printer ID should be unique.'
        ),
    ]

    @api.depends('status', 'computer_id.status')
    def _compute_printer_status(self):
        """ check computer and printer status
        """
        for rec in self:
            rec.online = rec.status in ['online'] and \
                rec.computer_id.status in ['connected']

    @api.depends('paper_ids', 'format_ids')
    def _compute_print_rules(self):

        def _html(message, icon='fa fa-question-circle-o'):
            return f'<span class="{icon}" title="{icon}"></span>'

        def _ok(message):
            return False, _html(message, 'fa fa-circle-o')

        def _error(message):
            return True, _html(message, 'fa fa-exclamation-circle')

        for printer in self:

            reports = self.env['printnode.rule'].search([
                ('printer_id', '=', printer.id)
            ]).mapped('report_id')

            errors = list(set(filter(None, [
                printer.printnode_check_report(report, False)
                for report in reports
            ] + [printer.printnode_check()])))

            if errors:
                printer.error, printer.notes = _error('\n'.join(errors))
            else:
                printer.error, printer.notes = _ok(_('Configuration is valid.'))

    @api.depends('name', 'computer_id.name')
    def _compute_display_name(self):
        for printer in self:
            printer.display_name = f'{printer.name} ({printer.computer_id.name})'

    def printnode_print(self, report_id, objects, copies=1, options=None, data=None):
        """
        This method is for preparing data for the "qweb-text" report types before sending it to
        the Printnode API. It can be called, for example, from print_scenario() and so on.
        """
        self.ensure_one()
        self.printnode_check_report(report_id)

        if not options:
            options = {}

        ids = objects and objects.mapped('id') or None
        content, content_type = report_id._render(
            report_ref=report_id.xml_id, res_ids=ids, data=data)

        data = {
            'printerId': self.printnode_id,
            'title': self._format_title(objects, copies),
            'source': self._get_source_name(),
            'contentType': self._get_content_type(report_id.report_type),
            'content': base64.b64encode(content).decode('ascii'),
            'qty': copies,
            'options': self._get_data_options(options),
        }

        res = self._post_printnode_job(data)

        # If model has printnode_printed flag and this flag is not inherited from other model
        # (through _inherits) mark records as printed
        if (
            'printnode_printed' in objects._fields
            and not objects._fields['printnode_printed'].inherited
        ):
            objects.write({
                'printnode_printed': True,
            })

        return res

    def printnode_print_b64(self, ascii_data, params, check_printer_format=True):
        """
        This method is for preparing data for the "qweb-pdf" and "py3o" ("pdf_base64") report types
        before sending it to the Printnode API. Used for printing via Actions -> Print, as well
        as for printing attachments, etc.
        """
        self.ensure_one()
        error = self.printnode_check(report=(check_printer_format and params))
        if error:
            raise UserError(error)

        printnode_data = {
            'printerId': self.printnode_id,
            'qty': params.get('copies', 1),
            'title': params.get('title'),
            'source': self._get_source_name(),
            'contentType': self._get_content_type(params.get('type')),
            'content': ascii_data,
            'options': self._get_data_options(params.get('options', {})),
        }
        return self._post_printnode_job(printnode_data)

    def printnode_check_report(self, report_id, raise_exception=True):
        """
        Check the print report for "exclude from auto printing" in the report policy.
        Call printnode_check() and raise the UserError exception if either check failed and
        raise_exception is True.
        """
        report_policy = self.env['printnode.report.policy'].search([
            ('report_id', '=', report_id.id),
        ])
        error = False

        if report_policy and report_policy.exclude_from_auto_printing:
            # We need to notify user in case he is trying to print report
            # that was excluded from printing
            error = _(
                'Your are trying to print report "{}".'
                ' But it was excluded from printing in "Report Settings" menu.'
            ).format(
                report_id.name,
            )

        report = {
            'title': report_policy and report_id.name,
            'type': report_policy and report_policy.report_type,
            'size': report_policy and report_policy.report_paper_id,
        }

        if not error:
            error = self.printnode_check(report)

        if error and raise_exception:
            self.printnode_logger(Constants.REPORTS_LOG_TYPE, str(error))
            raise UserError(error)

        return error

    def printnode_check_and_raise(self, report=None):
        """
        Call printnode_check method and raise the UserError exception if the check fails.
        """
        self.ensure_one()

        error = self.printnode_check(report)

        if error:
            self.printnode_logger(Constants.REPORTS_LOG_TYPE, str(error))
            raise UserError(error)

    def printnode_check(self, report=None):
        """ PrintNode Check
            eg. report = {'type': 'qweb-pdf', 'size': <printnode.format(0,)>}
        """

        # TODO: Refactor this method!

        self.ensure_one()

        # 1. check user settings

        if not self.env.company.printnode_enabled:
            return _(
                'Immediate printing via PrintNode is disabled for company %(company)s.'
                ' Please, contact Administrator to re-enable it.',
                company=self.env.company.name,
            )

        # 2. check printer settings

        if self.env.company.printnode_recheck and \
                not self.sudo().account_id.recheck_printer(self.sudo()):
            return _(
                'Printer %(printer)s is not available.'
                ' Please check it for errors or select another printer.',
                printer=self.name,
            )

        # 3. check report policies

        if not report:
            return None

        if not (set(REQUIRED_REPORT_KEYS).issubset(set(report.keys()))):
            return _(
                'Report expected three required parameters: %(keys)s. Make sure all of them '
                'passed correctly. Report: %(report)s.',
                keys=', '.join(REQUIRED_REPORT_KEYS),
                report=report,
            )

        report_types = [pf.qweb for pf in self.format_ids]

        if self.paper_ids and not report.get('size') and report.get('title'):
            return _(
                'Report %(report)s is not properly configured (no paper size).'
                ' Please update Report Settings or choose another report.',
                report=report.get('title'),
            )

        if self.paper_ids and report.get('size') \
                and report.get('size') not in self.paper_ids:
            return _(
                'Paper size for report %(title)s (%(size)s) and for printer %(name)s (%(paper)s)'
                ' do not match. Please update Printer or Report Settings.',
                title=report.get('title'),
                size=report.get('size').name,
                name=self.name,
                paper=', '.join([p.name for p in self.paper_ids]),
            )

        if report_types and report.get('type') \
                and report.get('type') not in report_types:
            formats = self.env['printnode.format'].search([
                ('qweb', '=', report.get('type'))
            ])
            return _(
                'Report type for report %(title)s (%(format)s) and for printer %(name)s (%(paper)s)'
                ' do not match. Please update Printer or Report Settings.',
                title=report.get('title'),
                format=', '.join([f.name for f in formats]),
                name=self.name,
                paper=', '.join([p.name for p in self.format_ids]),
            )

        return None

    def _create_printnode_job(self, data, force_commit=False) -> int:
        """
        Create a new printnode job with the provided data.

        :param data:            A dict of attrs of the request to create printjobs to the Printnode.
        :param force_commit:    A flag that indicates whether the printjob should be force committed
                                into the database.
        :return:                ID (int) of the created printjob.
        """

        title = data.get('title')
        printer_id = self.id
        content = data.get('content')
        content_type = data.get('contentType')

        printjob_id = None

        if force_commit:
            # The new cursor is used to create a printjob outside of the current transaction.
            # This provides access to the created print job (for example, through the controller)
            # immediately, without waiting for the current transaction to complete.
            db_registry = registry(self.env.cr.dbname)
            with db_registry.cursor() as cr:
                try:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    printjob_id = env['printnode.printjob'].create_job(
                        title, printer_id, content, content_type).id
                    cr.commit()
                except psycopg2.Error as exc:
                    _logger.exception(exc)
                    self.invalidate_cache()

        else:
            printjob_id = self.env['printnode.printjob'].sudo().create_job(
                title, printer_id, content, content_type).id

        return printjob_id

    def _post_printnode_job(self, data):
        """
        Send job into PrintNode. Return new job ID

        :param uri:     The Printnode URI to post printjobs.
        :param data:    A dict of attrs of the request to create printjobs to the Printnode.
                        This should contain the attributes needed by the PrintNode API to process
                        the printjob, such as: 'printerId', 'qty', 'title', 'source', 'contentType',
                        'content'.
        :return:        The printjob ID.
        """
        # Instance ID (int) of 'printnode.printjob' model
        printjob_id = self._create_printnode_job(
            data, force_commit=self.env.company.secure_printing)

        # Job ID from PrintNode API
        job_id = False

        auth = requests.auth.HTTPBasicAuth(
            self.account_id.api_key,
            self.account_id.password or ''
        )

        post_url = f'{self.account_id.endpoint}/{"printjobs"}'

        if self.env.company.secure_printing:
            data_content_type = 'pdf_uri' if data['contentType'] == 'pdf_base64' else 'raw_uri'

            content_url = self._build_printjob_content_url(printjob_id)

            data.update({
                'contentType': data_content_type,
                'content': content_url,
            })

        self.printnode_logger(
            log_type=Constants.REQUESTS_LOG_TYPE,
            log_string=f'POST request: {post_url}\n{data if data else None}',
        )
        resp = requests.post(
            post_url,
            auth=auth,
            json=data
        )

        if resp.status_code == 201:
            job_id = resp.json()
            self.printnode_logger(Constants.REQUESTS_LOG_TYPE, f'POST response: {job_id}')

            if self.env.company.secure_printing:
                db_registry = registry(self.env.cr.dbname)

                with db_registry.cursor() as cr:
                    try:
                        env = api.Environment(cr, SUPERUSER_ID, {})
                        env['printnode.printjob'].search([('id', '=', printjob_id)]).write({
                            'printnode_id': str(job_id)})
                        cr.commit()
                    except psycopg2.Error as exc:
                        _logger.exception(exc)
                        self.invalidate_cache()
                    else:
                        self.printnode_logger(
                            Constants.REQUESTS_LOG_TYPE,
                            f'Set "{job_id}" to "printnode_id" field for printjob_id:{printjob_id}'
                            'in "secure printing" mode.',
                        )
            else:
                printjob = self.env['printnode.printjob'].sudo().search([('id', '=', printjob_id)])
                printjob.sudo().write({'printnode_id': str(job_id)})
                self.printnode_logger(
                    Constants.REQUESTS_LOG_TYPE,
                    f'{job_id} was set for "printnode_id" field of printjob (id:{printjob_id}) in "safe print" mode.'  # NOQA
                )
        else:
            if 'application/json' in resp.headers.get('Content-Type'):
                message = resp.json().get('message', _('Something went wrong. Try again later'))
            else:
                message = _(
                    'Looks like printing service is currently unavailable. '
                    'Please contact us: support@ventor.tech'
                )

            raise UserError(_('Cannot send printjob: {}').format(message))

        return job_id

    def _format_title(self, objects, copies):
        if len(objects) == 1:
            return f'{objects.display_name}_{copies}'
        return f'{objects._description}_{len(objects)}_{copies}'

    def _get_source_name(self):
        full_version = self.env['ir.module.module'].sudo().search(
            [['name', '=', 'printnode_base']]).latest_version

        split_value = full_version and full_version.split('.')
        module_version = split_value and '.'.join(split_value[-3:])
        source_name = f'Odoo Direct Print PRO {module_version}'

        return source_name

    def _get_data_options(self, params=None):
        """Prepare print data options
        """
        options = {}
        if self.env.company.printnode_fit_to_page:
            options.update({'fit_to_page': False})
        if params:
            options.update(params)

        return options

    def _get_content_type(self, report_type=None):
        """Get content type
        """
        return 'pdf_base64' if report_type in ['qweb-pdf', 'py3o'] else 'raw_base64'

    def _build_printjob_content_url(self, printjob_id):
        """
        Build printjob content url to download document content ("secure printing").
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        # Time to live for printjob content URLs in minutes
        url_lifespan = self.env['ir.config_parameter'].sudo() \
            .get_param('printnode_base.printjob_content_url_lifespan')

        expiration_time = datetime.utcnow() + timedelta(minutes=int(url_lifespan))
        expiration_timestamp = round(expiration_time.timestamp())

        secret_key = self.env['ir.config_parameter'].sudo().get_param('database.secret')

        signature = hmac.new(
            secret_key.encode('UTF-8'),
            f'{printjob_id}{expiration_timestamp}'.encode('UTF-8'),
            hashlib.sha256
        ).hexdigest()

        dbname = quote_plus(self.env.cr.dbname)
        query_params = urlencode({
            'expires': str(expiration_timestamp),
            'signature': signature,
        })

        content_url = '{}/dpc/{}/printjob/{}/content?{}'.format(
            base_url,
            dbname,
            str(printjob_id),
            query_params
        )

        self.printnode_logger(
            Constants.REQUESTS_LOG_TYPE,
            f'Content url has been generated: {content_url}',
        )

        return content_url
