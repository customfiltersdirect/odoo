# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ['sale.order', 'printnode.mixin', 'printnode.scenario.mixin']

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

        if res is True:
            self.print_scenarios(action='print_document_on_sales_order')
            self.print_scenarios(action='print_picking_document_after_so_confirmation')

        return res

    def _scenario_print_picking_document_after_so_confirmation(
        self, report_id, printer_id, number_of_copies=1, **kwargs
    ):
        """
        Print picking document after SO confirmation
        """
        print_options = kwargs.get('options', {})

        # Print picking
        if self.warehouse_id.delivery_steps == 'ship_only':
            picking_type_to_print = self.warehouse_id.out_type_id
        else:
            picking_type_to_print = self.warehouse_id.pick_type_id

        picking_ids = self.picking_ids.filtered(
            lambda p: p.picking_type_id == picking_type_to_print)

        if picking_ids:
            printer_id.printnode_print(
                report_id,
                picking_ids,
                copies=number_of_copies,
                options=print_options,
            )
