from odoo import _, api, fields, models
import datetime
class ProductReplenish(models.Model):
    _inherit = 'product.template'


    def open_wizard(self):
        return {
            'name': 'Replenish',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            "view_type": "form",
            'res_model': 'product.replenish.wizard',
            'target': 'new',
            'view_id': self.env.ref('product_replenish.view_product_replenish_wizard').id,
            'context': {'default_product_ids': self.ids},
        }


