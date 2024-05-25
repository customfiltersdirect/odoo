from odoo import fields, models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    reserved_availability = fields.Float(
        'Quantity Reserved', compute='_compute_reserved_availability',
        digits='Product Unit of Measure',
        store=True,
        readonly=True, help='Quantity that has already been reserved for this move')

    def _compute_reserved_availability(self):
        """ Fill the `availability` field on a stock move, which is the actual reserved quantity
        and is represented by the aggregated `product_qty` on the linked move lines. If the move
        is force assigned, the value will be 0.
        """
        if not any(self._ids):
            # onchange
            for move in self:
                reserved_availability = sum(move.move_line_ids.mapped('product_qty'))
                move.reserved_availability = move.product_id.uom_id._compute_quantity(
                    reserved_availability, move.product_uom, rounding_method='HALF-UP')
        else:
            # compute
            result = {data['move_id'][0]: data['product_qty'] for data in
                      self.env['stock.move.line'].read_group([('move_id', 'in', self.ids)], ['move_id', 'product_qty'], ['move_id'])}
            for move in self:
                move.reserved_availability = move.product_id.uom_id._compute_quantity(
                    result.get(move.id, 0.0), move.product_uom, rounding_method='HALF-UP')