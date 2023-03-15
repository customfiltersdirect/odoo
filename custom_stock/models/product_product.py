from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    sale_order_comp_count = fields.Float()
