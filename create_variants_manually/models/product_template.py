from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_create_variants_overholt(self):
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.variants.overholt',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': False,
            'context': {
                'default_product_tmpl_id': self.id
            }
        }