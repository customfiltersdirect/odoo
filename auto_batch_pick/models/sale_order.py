# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """passing picking id to delivery order"""
        res = super(SaleOrder, self).action_confirm()
        self.create_batch()
        return res

    def create_batch(self):
        picking_types = self.env['stock.picking.type'].search([('code','=','outgoing')])
        pickings = self._search_pickings(picking_types)
        picking_length = len(pickings)
        if picking_length >=25:
            return self._create_batch(pickings)
        else:
            return False


    def _search_pickings(self, picking_types):
        no_of_orders = self.env['ir.config_parameter'].get_param('auto_batch_pick.auto_batch_orders') or 25

        return self.env["stock.picking"].search(
            [
                ("picking_type_id", "in", picking_types.ids),
                ("state", "in", ("assigned", "partially_available")),
                ("batch_id", "=", False),

            ],limit=no_of_orders
        )

    def _create_batch(self, pickings):
        return self.env["stock.picking.batch"].create(
            self._create_batch_values(pickings)
        )

    def _create_batch_values(self, pickings):
        return {"picking_ids": [(6, 0, pickings.ids)]}