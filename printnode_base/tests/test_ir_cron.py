# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestPrintNodeCommon


@tagged('post_install', '-at_install', 'pn_ir_cron')  # can be run by test-tag
class TestPrintNodeIrCron(TestPrintNodeCommon):
    """
    Tests of IrCron model methods
    """

    def setUp(self):
        super().setUp()

        self.scenario.update({
            'action': self.env.ref('printnode_base.print_product_labels_on_transfer').id,
            'report_id': self.env.ref('stock.label_product_product').id,
        })

        self.cron = self.env['ir.cron'].create({
            'active': False,
            'name': 'TestCronCreateMove',
            'user_id': self.env.ref('base.user_root').id,
            'model_id': self.env.ref('stock.model_stock_picking').id,
            'state': 'code',
            'code': 'model.search([("name", "=", "Test Stock Picking")]).button_validate()',
            'interval_number': 1,
            'interval_type': 'days',
            'numbercall': 1,
            'doall': False,
        })

        # Create Mock objects
        self.mock_scenario_print_product_labels_on_transfer = self._create_patch_object(
            type(self.stock_picking),
            '_scenario_print_product_labels_on_transfer',
        )
        self.mock_scenario_print_product_labels_on_transfer.return_value = True

        self.mock_get_printer = self._create_patch_object(
            type(self.scenario),
            '_get_printer',
        )

    def _set_up_stock_move(self):
        self.stock_move._action_confirm()
        self.stock_move._action_assign()
        self.stock_move.move_line_ids.quantity = 2

    def test_run_print_scenario_from_cron_case_1(self):
        """ Test to check run/skip print scenario from cron
        """

        # Set Up
        self._set_up_stock_move()

        # Printnode is disabled at company level - print scenario won't run.
        # Transaction will be completed.
        self.company.printnode_enabled = False
        self.cron.active = True

        self.assertFalse(self.product_id.stock_quant_ids)

        self.cron._callback(self.cron.name, self.cron.ir_actions_server_id.id, "New_job_id")

        self.assertEqual(
            self.product_id.stock_quant_ids.filtered(
                lambda q: q.location_id == self.location_dest)[:1].quantity,
            2,
        )
        self.mock_scenario_print_product_labels_on_transfer.assert_not_called()
        self.mock_get_printer.assert_not_called()

    @patch('odoo.addons.printnode_base.models.ir_cron.ir_cron.with_context')
    def test_run_print_scenario_from_cron_case_2(self, mock_with_context):
        """ Test to check run/skip print scenario from cron
        """

        # Set Up
        self._set_up_stock_move()
        # Mock with_context() to avoid context substitution
        # in the method _callback
        mock_with_context.return_value = self.cron

        # Printing scenarios from crons is disabled for current company - print
        # scenario won't run.
        self.company.printnode_enabled = True
        self.company.printing_scenarios_from_crons = False
        self.cron.active = True

        self.assertFalse(self.product_id.stock_quant_ids)

        self.cron._callback(self.cron.name, self.cron.ir_actions_server_id.id, "New_job_id")

        self.assertEqual(
            self.product_id.stock_quant_ids.filtered(
                lambda q: q.location_id == self.location_dest)[:1].quantity,
            2,
        )
        self.mock_scenario_print_product_labels_on_transfer.assert_not_called()
        self.mock_get_printer.assert_not_called()

    def test_run_print_scenario_from_cron_case_3(self):
        """ Test to check run/skip print scenario from cron
        """

        # Set Up
        self._set_up_stock_move()
        self.mock_get_printer.return_value = self.printer, self.printer_bin

        # Print scenario will be run, transaction will be completed.
        self.company.printnode_enabled = True
        self.company.printing_scenarios_from_crons = True
        self.cron.active = True

        self.assertFalse(self.product_id.stock_quant_ids)

        self.cron._callback(self.cron.name, self.cron.ir_actions_server_id.id, "New_job_id")

        self.assertEqual(
            self.product_id.stock_quant_ids.filtered(
                lambda q: q.location_id == self.location_dest)[:1].quantity,
            2,
        )
        self.mock_scenario_print_product_labels_on_transfer.assert_called_once()
        self.mock_get_printer.assert_called_once()

    def test_run_print_scenario_from_cron_case_4(self):
        """ Test to check run/skip print scenario from cron
        """

        # Set Up
        self._set_up_stock_move()
        self.mock_get_printer.return_value = None
        self.mock_get_printer.side_effect = UserError("Test Exception - UserError")

        # _get_printer() method from scenario returned Exception - print scenario won't run,
        # but transaction will be completed.
        self.company.printnode_enabled = True
        self.company.printing_scenarios_from_crons = True
        self.cron.active = True

        self.assertFalse(self.product_id.stock_quant_ids)

        self.cron._callback(self.cron.name, self.cron.ir_actions_server_id.id, "New_job_id")

        self.assertEqual(
            self.product_id.stock_quant_ids.filtered(
                lambda q: q.location_id == self.location_dest)[:1].quantity,
            2,
        )
        self.mock_scenario_print_product_labels_on_transfer.assert_not_called()
        self.mock_get_printer.assert_called_once()
