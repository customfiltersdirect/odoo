from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    reserved_availability = fields.Float(
        'Quantity Reserved', compute='_compute_reserved_availability',
        digits='Product Unit of Measure',
        store=True,
        readonly=True, help='Quantity that has already been reserved for this move')
