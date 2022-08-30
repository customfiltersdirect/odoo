# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

import re
import requests
import psycopg2

from odoo import api, exceptions, fields, models, registry, SUPERUSER_ID, _

# Copied from request library to provide compatibility with the library
try:
    from simplejson import JSONDecodeError
except ImportError:
    from json import JSONDecodeError


class PrintNodeAccount(models.Model):
    """ PrintNode Account entity
    """
    _name = 'printnode.account'
    _description = 'PrintNode Account'

    alias = fields.Char(
        string='Alias'
    )

    computer_ids = fields.One2many(
        'printnode.computer',
        'account_id',
        string='Computers'
    )

    endpoint = fields.Char(
        string='Endpoint',
        required=True,
        readonly=True,
        default='https://api.printnode.com/'
    )

    limits = fields.Integer(
        string='Plan Page Limits',
        readonly=True,
    )

    name = fields.Char(
        string='Name',
        default='Default Account',
    )

    debug_logging = fields.Boolean(
        string='Debug logging',
        default=False,
        help='By enabling this feature, all requests will be logged. '
             'You can find them in "Settings - Technical - Logging" menu.',
    )

    password = fields.Char(
        string='Password',
        required=False
    )

    printed = fields.Integer(
        string='Printed Pages',
        readonly=True,
    )

    printnode_id = fields.Integer('Direct Print ID')

    status = fields.Char(
        string='Status',
        compute='_compute_account_status',
        store=True,
        readonly=True
    )

    api_key = fields.Char(
        string='API Key',
        required=True
    )

    is_dpc_account = fields.Boolean(
        "Is Direct Print Client Account",
        default=False,
    )

    is_allowed_to_collect_data = fields.Boolean(
        "Allow to collect stats",
        default=False,
    )

    _sql_constraints = [
        ('printnode_id', 'unique(printnode_id)', 'Account already exists.'),
        ('api_key', 'unique(api_key)', 'API Key (token) must be unique.'),
    ]

    @api.model
    def create(self, vals):
        account = super(PrintNodeAccount, self).create(vals)

        account.import_devices()

        return account

    def write(self, vals):
        activate_account = False

        if 'api_key' in vals:
            # When API Key changed - activate the account
            if vals['api_key'] != self.api_key:
                activate_account = True

        res = super(PrintNodeAccount, self).write(vals)

        if activate_account:
            self.activate_account()

        return res

    def activate_account(self):
        # Remove computers and devices connected to current account
        self.unlink_devices()

        base_module = self.env['ir.module.module'].search([['name', '=', 'base']])
        odoo_version = base_module.latest_version.split('.')[0]

        params = {
            "type": "odoo",
            "version": odoo_version,
            "identifier": self.env['ir.config_parameter'].sudo().get_param('database.uuid'),
            "action": "activate"
        }

        # Activate through DPC service
        response = self._send_dpc_request('PUT', f'api-key-activations/{self.api_key}', json=params)

        # Any request errors
        if not response:
            # No response means that DPC API is not responding or something went wrong.
            # It is better to try activate through PrintNode API instead of activation error

            # We do not know for sure
            self.is_dpc_account = None

            # But can try to activate through PrintNode
            if self._is_correct_dpc_api_key():
                self.update_limits_for_account()
                self.import_devices()

                return

            raise exceptions.UserError(
                _(
                    'Wrong API Key provided. Please, provide the correct key or '
                    'check Direct Print / Settings page for details.\n\n'
                    'Error details: {}'
                ).format(self.status)
            )

        # Everything is okay: the key is from DPC
        if response.get('status_code', 200) == 200:
            self.is_dpc_account = True
            self.update_limits_for_account()
            self.import_devices()

            return

        # Status 404 means that it can be PrintNode API Key but we do not have it in DPC DB
        # User can provide Printnode API key (with no use of our service)
        if response.get('status_code', 200) == 404:
            self.is_dpc_account = False

            if self._is_correct_dpc_api_key():
                self.update_limits_for_account()
                self.import_devices()

                return

        # Something is wrong with the key
        self.status = response.get('message', 'Something went wrong')
        self.env.cr.commit()

        raise exceptions.UserError(
            _(
                'Wrong API Key provided. Please, provide the correct key or '
                'check Direct Print / Settings page for details.\n\n'
                'Error details: {}'
            ).format(self.status)
        )

    @api.model
    def get_limits(self):
        limits = []
        for rec in self.env['printnode.account'].search([]):
            if rec.status == 'OK':
                limits.append({
                    'account': rec.name or rec.api_key[:10] + '...',
                    'printed': rec.printed,
                    'limits': rec.limits,
                })
            else:
                limits.append({
                    'account': rec.name or rec.api_key[:10] + '...',
                    'error': rec.status,
                })
        return limits

    def import_devices(self):
        """ Re-import list of printers into OpenERP.
        """
        computers = self._send_printnode_request('computers') or []

        self._deactivate_devices()

        for computer in computers:
            odoo_computer = self._get_node('computer', computer, self.id)
            get_printers_url = 'computers/{}/printers'.format(computer['id'])

            # Downloading printers with tray bins
            for printer in self._send_printnode_request(get_printers_url):
                odoo_printer = self._get_node('printer', printer, odoo_computer.id)

                # Splitted to 2 checks because capabilities can include None values in some cases
                if printer.get('capabilities') and printer.get('capabilities').get('bins'):
                    for bin_name in printer.get('capabilities', {}).get('bins'):
                        bin_values = {'name': bin_name, 'printer_id': odoo_printer.id}
                        existing_bin = self.env['printnode.printer.bin'].search(
                            [('name', '=', bin_name), ('printer_id', '=', odoo_printer.id)],
                            limit=1,
                        )
                        if not existing_bin:
                            self.env['printnode.printer.bin'].create(bin_values)

            # Downloading scales
            get_scales_url = 'computer/{}/scales'.format(computer['id'])
            for scales in self._send_printnode_request(get_scales_url):
                self._create_or_update_scales(scales, odoo_computer)

    def _create_or_update_scales(self, scales, odoo_computer):
        scales_env = self.env['printnode.scales']
        existing_scales = scales_env.with_context(active_test=False).search([
            ('printnode_id', '=', scales['productId']),
            ('computer_id', '=', odoo_computer.id)
        ], limit=1)

        if existing_scales:
            existing_scales.write({
                'name': scales['deviceName'],
                'status': 'online',
            })
        else:
            scales_vals = {
                'name': scales['deviceName'],
                'device_num': scales['deviceNum'],
                'printnode_id': scales['productId'],
                'computer_id': odoo_computer.id,
                'status': 'online',
            }
            scales_env.create(scales_vals)

    def recheck_printer(self, printer, print_sample_report=False):
        """ Re-check particular printer status
        """
        uri = 'printers/{}'.format(printer.printnode_id)

        resp = self._send_printnode_request(uri)
        printer.write({
            'status': resp
                and resp[0]['computer']['state'] == 'connected'  # NOQA
                and resp[0]['state']  # NOQA
                or 'offline'  # NOQA
        })

        return printer.online

    def unlink_devices(self):
        """
        Delete computers, printers, print jobs and user rules
        """
        for computer in self.with_context(active_test=False).computer_ids:
            for rule in self.env['printnode.rule'].search([
                ('printer_id', 'in', computer.printer_ids.ids),
            ]):
                rule.unlink()
            for printer in computer.printer_ids:
                for job in printer.printjob_ids:
                    job.unlink()
                printer.unlink()
            computer.unlink()

    def update_limits_for_account(self):
        """
        Update limits and number of printed documents through API
        """
        if self.is_dpc_account:
            printed, limits = self._get_limits_dpc()
        else:
            printed, limits = self._get_limits_printnode()

        # Update data
        self.printed = printed
        self.limits = limits

    def update_limits(self):
        """
        Update limits and number of printed documents through API
        """
        for rec in self.env['printnode.account'].search([]):
            rec.update_limits_for_account()

        # Notify user if number of available pages too low
        self._notify_about_limits()

    def update_main_account(self, api_key, is_allowed_to_collect_data=True):
        """
        Update an existing or create a new main account.
        The main account is the account with lowest ID.
        """
        main_account = None
        accounts = self.env['printnode.account'].search([]).sorted(key=lambda r: r.id)

        if accounts:
            main_account = accounts[0]

            if not api_key:
                # Remove account
                main_account.unlink()
            else:
                # Update account
                if main_account.api_key != api_key:
                    main_account.api_key = api_key
                    main_account.is_allowed_to_collect_data = is_allowed_to_collect_data
        else:
            if api_key:
                main_account = self.env['printnode.account'].create({
                    'api_key': api_key,
                    'is_allowed_to_collect_data': is_allowed_to_collect_data,
                })
                main_account.activate_account()

        return main_account

    @api.depends('endpoint', 'api_key', 'password')
    def _compute_account_status(self):
        """ Request PrintNode account details - whoami
        """
        for rec in self.filtered(lambda x: x.endpoint and x.api_key):
            rec._send_printnode_request('whoami')

    def _get_node(self, node_type, node_id, parent_id):
        """ Parse and update PrintNode nodes (printer and computers)
        """
        node = self.env['printnode.{}'.format(node_type)].with_context(active_test=False).search([
            ('printnode_id', '=', node_id['id']),
        ], limit=1)

        if not node:
            params = {
                'printnode_id': node_id['id'],
                'name': node_id['name'],
                'status': node_id['state'],
            }
            if node_type == 'computer':
                params.update({'account_id': parent_id})
            if node_type == 'printer':
                params.update({'computer_id': parent_id})

            node = node.create(params)
        else:
            node.write({
                'name': node_id['name'],
                'status': node_id['state'],
            })

        return node

    def log_debug(self, log_string, function_name):
        self.ensure_one()

        if self.debug_logging:
            self.flush()
            db_name = self._cr.dbname

            # Use a new cursor to avoid rollback that could be caused by an upper method
            try:
                db_registry = registry(db_name)
                with db_registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    logging_object = env['ir.logging']
                    logging_object.sudo().create({
                        'name': 'direct.print',
                        'type': 'server',
                        'dbname': db_name,
                        'level': 'DEBUG',
                        'message': log_string,
                        'path': 'odoo_direct_print_pro',
                        'func': function_name,
                        'line': 1}
                    )
            except psycopg2.Error:
                pass

    def _send_printnode_request(self, uri):
        """
        Send request with basic authentication and API key
        """
        auth = requests.auth.HTTPBasicAuth(self.api_key, self.password or '')
        if self.endpoint.endswith('/'):
            self.endpoint = self.endpoint[:-1]

        try:
            function_name = uri.replace('/', '_')
            request_url = '{}/{}'.format(self.endpoint, uri)
            self.log_debug(request_url, 'printnode_get_request_%s' % function_name)
            resp = requests.get(request_url, auth=auth)

            # 403 is a HTTP status code which can be returned for child accounts in some cases
            # like checking printing limits on PrintNode
            if resp.status_code not in (200, 403):
                resp.raise_for_status()

            if self.status != 'OK':
                self.status = 'OK'

            json_response = resp.json()

            self.log_debug(json_response, 'printnode_get_response_%s' % function_name)

            return json_response

        except requests.exceptions.ConnectionError as e:
            # Deactivate printers only from current account
            self._deactivate_printers()

            self.status = e
        except requests.exceptions.RequestException as e:
            # Deactivate printers only from current account
            self._deactivate_printers()

            self.status = e

        return None

    def _send_dpc_request(self, method, uri, **kwargs):
        """
        Send request to DPC API with API key
        """
        methods = {
            'GET': requests.get,
            'POST': requests.post,
            'PUT': requests.put,
        }

        if method not in methods:
            raise ValueError('Bad HTTP method')

        dpc_url = self.env['ir.config_parameter'].sudo().get_param('printnode_base.dpc_api_url')

        try:
            resp = methods[method]('{}/{}'.format(dpc_url, uri), **kwargs)

            if self.status != 'OK':
                self.status = 'OK'
            return resp.json()
        except requests.exceptions.ConnectionError as e:
            self._deactivate_printers()

            self.status = e
        except requests.exceptions.RequestException as e:
            self._deactivate_printers()

            self.status = e
        except JSONDecodeError as e:
            self._deactivate_printers()

            self.status = e

        return None

    def _is_correct_dpc_api_key(self):
        """
        Checks whether API key related to Printnode account
        """
        response = self._send_printnode_request('whoami')
        return bool(response)

    def _get_limits_dpc(self):
        """
        Get status and limits (printed pages + total available pages)
        for Direct Print Client account
        """
        printed = 0
        limits = 0

        response = self._send_dpc_request('GET', f'api-keys/{self.api_key}')

        if response.get('status_code', 500) == 200:
            stats = response['data']['stats']
            printed = stats.get('printed', 0)
            limits = stats.get('limits', 0)
        else:
            self.status = response.get('message', 'Something went wrong')

        return printed, limits

    def _get_limits_printnode(self):
        """
        Get limits (printed pages + total available pages) from Printnode through API
        """
        printed = 0
        limits = 0

        stats = self._send_printnode_request('billing/statistics')

        # Unavailable for child PrintNode accounts
        if stats and 'current' in stats:
            printed = stats['current'].get('prints', 0)

        plan = self._send_printnode_request('billing/plan')

        # Unavailable for child PrintNode accounts
        if plan and 'current' in plan:
            raw_limits = plan['current'].get('printCurve')
            if raw_limits:
                # Parse with regex value like '("{0,5000}","{0,0}",0.0018)
                m = re.match(r'\(\"{(?P<_>\d+),(?P<limits>\d+)}\",.*\)', raw_limits)
                limits = (m and m.group('limits')) or 0

        return printed, limits

    def _notify_about_limits(self):
        """
        Check conditions and notify the customer if limits are close to exceed
        """
        company = self.env.user.company_id

        if company.printnode_notification_email and company.printnode_notification_page_limit:
            accounts_to_notify = self.env['printnode.account'].search([]).filtered(
                lambda r: r.limits > 0
                    and (r.limits - r.printed) < company.printnode_notification_page_limit)  # NOQA

            if accounts_to_notify:
                context = self.env.context.copy()
                context.update({'accounts': accounts_to_notify})

                mail_template = self.env.ref('printnode_base.reaching_limit_notification_email')
                mail_template.with_context(context).send_mail(company.id, force_send=True)

    def _deactivate_printers(self):
        """
        Deactivate printers only from current account
        """
        self.ensure_one()

        domain = [['computer_id', 'in', self.computer_ids.ids]]
        self.env['printnode.printer'].with_context(active_test=False)\
            .search(domain).write({'status': 'offline'})

    def _deactivate_devices(self):
        """
        Deactivate scales
        """
        self.env['printnode.scales'].search([]).write(
            {'status': 'offline'},
        )
