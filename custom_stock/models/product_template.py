from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qty_available = fields.Float(
        'Quantity On Hand', compute='_compute_quantities', search='_search_qty_available',
        compute_sudo=False, digits='Product Unit of Measure', store=False)
    qty_available_cy = fields.Float('Quantity On Hand', compute='_compute_quantity_cy', store=True)

    @api.depends('qty_available')
    def _compute_quantity_cy(self):
        for rec in self:
            rec.write({'qty_available_cy': rec.qty_available})
