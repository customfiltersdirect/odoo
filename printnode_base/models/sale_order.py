# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, _


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ['sale.order', 'printnode.mixin', 'printnode.scenario.mixin']

    def action_confirm(self):
        """ Overriding the default method to add custom logic with print scenarios for
            confirm sale orders.
        """
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
        printed = False

        # Print picking
        if self.warehouse_id.delivery_steps == 'ship_only':
            picking_type_to_print = self.warehouse_id.out_type_id
        else:
            picking_type_to_print = self.warehouse_id.pick_type_id

        picking_ids = self.picking_ids.filtered(
            lambda p: p.picking_type_id == picking_type_to_print)

        if picking_ids:
            printed = printer_id.printnode_print(
                report_id,
                picking_ids,
                copies=number_of_copies,
                options=print_options,
            )

        return printed

    def open_print_order_line_reports_wizard(self):
        """ Returns action window with 'Print Order Lines Reports Wizard'
        """
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Print Order Lines Reports Wizard'),
            'res_model': 'printnode.print.sale.order.line.reports.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'printnode_base.printnode_print_sale_order_line_reports_wizard_form').id,
            'target': 'new',
            'context': self.env.context,
        }
