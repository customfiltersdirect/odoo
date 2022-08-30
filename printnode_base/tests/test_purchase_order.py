# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from datetime import datetime
from unittest.mock import patch, call

from odoo.tests import tagged

from .common import TestPrintNodeCommon


@tagged('post_install', '-at_install', 'pn_purchase_order')  # can be run by test-tag
class TestPrintNodePurchaseOrder(TestPrintNodeCommon):
    """Tests of StockPicking model methods"""

    def setUp(self):
        super(TestPrintNodePurchaseOrder, self).setUp()

        self.po_report = self.env['ir.actions.report'].search([
            ('name', '=', 'Purchase Order'),
        ], limit=1)

        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env['product.product'].create({'name': 'Large Desk'})
        self.purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_qty': 5.0,
                    'product_uom': self.product.uom_po_id.id,
                    'price_unit': 100.0,
                    'date_planned': datetime.today(),
                    'taxes_id': False,
                })],
        })

    def test_scenario_print_picking_document_after_po_confirmation(self):
        """
        Test printing picking document after PO confirmation
        """

        with self.cr.savepoint(), patch.object(type(self.printer), 'printnode_print') \
                as mock_printnode_print:
            self.purchase_order._scenario_print_picking_document_after_po_confirmation(
                self.po_report,
                self.printer,
            )
            mock_printnode_print.assert_called_once_with(
                self.po_report,
                self.purchase_order.picking_ids,
                copies=1,
                options={},
            )

    def test_button_confirm(self):
        """
        Test running print scenarios:
        - print_document_on_purchase_order
        - print_picking_document_after_po_confirmation
        after PO validation
        """

        with self.cr.savepoint(), patch.object(type(self.purchase_order), 'print_scenarios') \
                as mock_print_scenarios:

            self.purchase_order.button_confirm()
            self.assertEqual(
                mock_print_scenarios.call_args_list,
                [
                    call(action='print_document_on_purchase_order'),
                    call(action='print_picking_document_after_po_confirmation')
                ]
            )
