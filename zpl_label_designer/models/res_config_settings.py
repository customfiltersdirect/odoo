import secrets

from odoo import api, fields, models


API_KEY_SIZE = 20  # in bytes


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    zld_allowed_models = fields.Many2many(
        'ir.model',
        readonly=False,
        related='company_id.zld_allowed_models',
    )

    zld_api_key = fields.Char(
        string='ZLD API Key',
        compute='_compute_zld_api_key',
        help='API key for the access from ZPL Label Designer',
    )

    def _compute_zld_api_key(self):
        """
        Update API key for all config settings
        """
        for record in self:
            record.zld_api_key = self.get_zld_api_key()

    def generate_zld_api_key(self):
        """
        Generate API key to use for API requests from designer to Odoo.
        """
        api_key = secrets.token_hex(API_KEY_SIZE)
        self.env['ir.config_parameter'].sudo().set_param('zpl_label_designer.api_key', api_key)
        return

    def get_values(self):
        """
        Get values for the installed integration.
        """
        res = super(ResConfigSettings, self).get_values()

        zld_api_key = self.get_zld_api_key()
        res.update(zld_api_key=zld_api_key)

        return res

    @api.model
    def get_zld_api_key(self):
        """
        Get API key for the installed integration.
        """
        return self.env['ir.config_parameter'].sudo().get_param('zpl_label_designer.api_key')
