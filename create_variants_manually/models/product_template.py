from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _create_variant_ids(self):
        line_attributes = self.valid_product_template_attribute_line_ids
        if line_attributes:
            all_never = all([line.attribute_id.create_variant == "no_variant" for line in line_attributes if line.active])
            if all_never:
                return False
        return super()._create_variant_ids()

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