from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qty_available = fields.Float(
        'Quantity On Hand', compute='_compute_quantities', search='_search_qty_available',
        compute_sudo=False, digits='Product Unit of Measure', store=True)
