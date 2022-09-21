# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.
from odoo import api, exceptions, fields, models, _
from requests.models import PreparedRequest


class PrintnodeInstaller(models.TransientModel):
    """
    Used to set API key to use Printnode module
    """
    _name = 'printnode.installer'
    _description = 'Direct Print API Key Installer'

    api_key = fields.Char(
        string='API Key',
    )

    is_allowed_to_collect_data = fields.Boolean(
        string='Collect statistics',
        default=True,
    )

    state = fields.Selection(
        selection=[
            ('introduction', 'Introduction'),
            ('settings', 'Settings'),
        ],
        string="Current Step",
        default="introduction",
        readonly=True
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        accounts = self.env['printnode.account'].search([]).sorted(key=lambda r: r.id)

        if accounts:
            # First account is main account. All other accounts - not allowed anymore
            # (but will still work for better customer experience)
            account = accounts[0]

            res['api_key'] = account.api_key
            res['is_allowed_to_collect_data'] = account.is_allowed_to_collect_data

        return res

    def save_settings(self):
        if not self.api_key:
            raise exceptions.UserError(_('Please, enter the valid API key'))

        self.env['printnode.account'].update_main_account(
            self.api_key,
            self.is_allowed_to_collect_data)

        return {
            'name': _('Direct Print Client Settings'),
            'type': 'ir.actions.act_window',
            'target': 'inline',
            'view_mode': 'form',
            'res_model': 'res.config.settings',
            'context': {'module': 'printnode_base'},
        }

    def get_api_key(self):
        """
        Redirect the user to the Direct Print Client platform
        """
        portal_base_url = self.env['ir.config_parameter'].sudo().get_param('printnode_base.dpc_url')
        odoo_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        portal_url = '{}/get-api-key'.format(portal_base_url)
        controller_url = '{}/dpc-callback'.format(odoo_base_url)

        # Requests lib used to simplicity
        request = PreparedRequest()
        request.prepare_url(portal_url, {'redirect_url': controller_url})

        return {
            'type': 'ir.actions.act_url',
            'url': request.url,
            'target': 'self',
        }

    def show_settings(self):
        self.state = 'settings'

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def show_introduction(self):
        self.state = 'introduction'

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
