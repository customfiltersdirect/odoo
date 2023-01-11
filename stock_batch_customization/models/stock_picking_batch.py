# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
import collections


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    grouped_transfer_ids = fields.One2many('group.move.line', 'batch_id', string='Stock move lines')

    def action_grouped_transfer(self):
        self.grouped_transfer_ids = [(5, 0, 0)]  # Remove all previous groups
        product_ids = set()
        location_ids = set()
        for move_line in self.move_line_ids:
            line_ids = self.move_line_ids.filtered(lambda x: x.product_id == move_line.product_id and x.location_id == move_line.location_id)
            qty = 0
            for line in line_ids:
                qty += line.product_uom_qty
            qty_done = 0
            for line in line_ids:
                qty_done += line.qty_done
            groups = self.grouped_transfer_ids.filtered(lambda x: x.product_id == move_line.product_id and x.location_id == move_line.location_id)
            # if move_line.product_id.id not in product_ids or move_line.location_id.id not in location_ids:
            if not groups:
                self.env['group.move.line'].create({
                    'product_id': move_line.product_id.id,
                    'product_uom_qty': qty,
                    'product_uom_id': move_line.product_id.uom_id.id,
                    'location_id': move_line.location_id.id,
                    'location_dest_id': move_line.location_dest_id.id,
                    'qty_done': qty_done,
                    'company_id': move_line.company_id.id,
                    'lot_id': move_line.lot_id.id,
                    'lot_name': move_line.lot_name,
                    'state': move_line.state,
                    'batch_id': self.id
                })
            product_ids.add(move_line.product_id.id)
            location_ids.add(move_line.location_id.id)
