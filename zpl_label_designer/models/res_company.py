from odoo import api, fields, models


ALLOWED_MODELS_TO_ZLD_LABEL = [
    "product.product", "product.template",
    "stock.lot", "stock.quant.package"
]


class Company(models.Model):
    _inherit = 'res.company'

    zld_allowed_models = fields.Many2many(
        'ir.model',
        string='Allowed models to "ZPL Label Designer"',
    )

    @api.model
    def _set_default_zld_allowed_models(self):
        """
        Set default models for the 'zld_allowed_models' field for all existing companies
        """
        allowed_model_ids = self.env['ir.model'].search([(
            "model", "in", ALLOWED_MODELS_TO_ZLD_LABEL)])

        for company in self.env['res.company'].search([]):
            company.sudo().zld_allowed_models = [
                (4, model_id.id) for model_id in allowed_model_ids]
