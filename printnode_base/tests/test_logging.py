# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestPrintNodeCommon


@tagged('post_install', '-at_install', 'pn_logging')  # can be run by test-tag
class TestPrintNodeLogger(TestPrintNodeCommon):
    """
    Tests of LoggerMixin model methods
    """

    def setUp(self):
        super().setUp()

        self.stock_picking_2 = self.env['stock.picking'].create({
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.location_dest.id,
            'move_type': 'direct',
            'picking_type_id': self.picking_type_incoming.id,
            'name': "Test Stock Picking #2",
        })

        self.scenario.update({
            'action': self.env.ref('printnode_base.print_product_labels_on_transfer').id,
            'report_id': self.env.ref('stock.label_product_product').id,
        })

        self.user.printnode_enabled = True

        self.company.printnode_enabled = True

        # Create Mock objects
        self.mock_scenario_print_product_labels_on_transfer = self._create_patch_object(
            type(self.stock_picking),
            '_scenario_print_product_labels_on_transfer',
        )
        self.mock_scenario_print_product_labels_on_transfer.return_value = True

        self.mock_scenario_get_printer = self._create_patch_object(
            type(self.env['printnode.scenario']),
            '_get_printer',
        )
        self.mock_scenario_get_printer.return_value = self.printer, self.printer_bin

        self.mock_write_logs = self._create_patch_object(
            type(self.env['printnode.logger.mixin']),
            '_write_logs',
        )

    def test_printnode_logger(self):
        """ Test to check of logging
        """

        # Set Up
        self.company.debug_logging = True
        self.company.log_type_ids = [
            (6, 0, [self.env.ref('printnode_base.printnode_log_type_scenarios').id])]
        Picking = self.env['stock.picking']

        # Case 1: Normal logging of print scenarios
        Picking.with_user(self.user).print_scenarios(
            'print_product_labels_on_transfer',
            ids_list=[self.stock_picking.id, self.stock_picking_2.id],
        )

        self.assertEqual(self.mock_write_logs.call_count, 4)

        # Case 2: UserError expected
        self.mock_scenario_get_printer.side_effect = UserError("Test UserError")

        with self.assertRaises(UserError):
            Picking.with_user(self.user).print_scenarios(
                'print_product_labels_on_transfer',
                ids_list=[self.stock_picking.id, self.stock_picking_2.id],
            )

            self.assertEqual(self.mock_write_logs.call_count, 4)
