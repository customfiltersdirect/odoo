# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import api, models


class StockMoveLine(models.Model):
    _name = 'stock.move.line'
    _inherit = ['stock.move.line', 'printnode.mixin', 'printnode.scenario.mixin']

    @api.model_create_multi
    def create(self, vals_list):
        mls = super().create(vals_list)

        self._call_scenarios(mls)

        return mls

    def write(self, vals):
        changed_move_lines = self.env['stock.move.line']
        for move_line in self:
            if 'qty_done' in vals:
                qty_change = vals.get('qty_done') - move_line.qty_done
                if qty_change:
                    changed_move_lines |= move_line

        res = super().write(vals)

        self._call_scenarios(changed_move_lines)

        return res

    def _call_scenarios(self, mls):
        # These scenarios shouldn't be run from crons
        if mls and not self.env.context.get('from_cron', False):
            self.print_scenarios(
                action='print_single_lot_label_on_transfer',
                ids_list=mls.mapped('picking_id.id'),
                new_move_lines=mls)

            self.print_scenarios(
                action='print_multiple_lot_labels_on_transfer',
                ids_list=mls.mapped('picking_id.id'),
                new_move_lines=mls)

            self.print_scenarios(
                action='print_single_product_label_on_transfer',
                ids_list=mls.mapped('picking_id.id'),
                new_move_lines=mls)

            self.print_scenarios(
                action='print_multiple_product_labels_on_transfer',
                ids_list=mls.mapped('picking_id.id'),
                new_move_lines=mls)
