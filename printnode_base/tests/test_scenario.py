# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from unittest.mock import patch, call

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestPrintNodeCommon, SECURITY_GROUP


@tagged('post_install', '-at_install', 'pn_scenario')  # can be run by test-tag
class TestPrintNodeScenario(TestPrintNodeCommon):
    """
    Tests of Scenario model methods
    """

    def setUp(self):
        super(TestPrintNodeScenario, self).setUp()

        self.picking_report = self.env['ir.actions.report'].search([
            ('name', '=', 'Picking Operations'),
        ], limit=1)

        self.user_rule.update({'printer_bin': self.printer_bin.id})

        self.scenario.update({'report_id': self.report.id})

        self.stock_picking = self.env['stock.picking'].create({
            'location_id': self.env['stock.location'].create({
                'name': 'Test_location',
                'usage': 'internal'
            }).id,
            'location_dest_id': self.env['stock.location'].create({
                'name': 'Test_dest_location',
                'usage': 'customer'
            }).id,
            'move_type': 'direct',
            'picking_type_id': self.env['stock.picking.type'].create({
                'code': 'internal',
                'company_id': self.company.id,
                'name': 'Test_picking_type',
                'sequence_code': 'TEST',
                'warehouse_id': self.env['stock.warehouse'].create({
                    'partner_id': self.env['res.partner'].create({'name': 'Test Partner'}).id,
                    'name': 'Test_warehouse',
                    'code': 'Test',
                }).id,
            }).id,
        })

    def test_check_number_of_copies(self):
        """
        Test copy limit > 1
        """

        with self.assertRaises(UserError):
            self.scenario.number_of_copies = 0

    def test_onchange_printer(self):
        """
        Test reset printer_bin field
        """

        self.assertNotEqual(self.scenario.printer_bin, self.printer_bin)
        self.printer.default_printer_bin = self.printer_bin.id
        self.scenario.printer_id = self.printer.id
        self.scenario._onchange_printer()
        self.assertEqual(self.scenario.printer_bin, self.printer_bin)

    def test_onchange_action(self):
        """
        Test reset report_id field
        """

        self.assertEqual(self.scenario.action, self.scenario_action)
        self.assertEqual(self.scenario.report_id, self.report)
        self.scenario._onchange_action()
        self.assertNotEqual(self.scenario.report_id, self.report)

    def test_apply_domain(self):
        """
        Test for getting objects by identifiers with applied domain
        """

        test_ids_list = self.env[self.scenario.model_id.model].search([]).ids
        test_objects = self.env[self.scenario.model_id.model].browse(test_ids_list)
        self.assertEqual(test_objects, self.scenario._apply_domain(test_ids_list))

        test_so = self.env[self.scenario.model_id.model].create({
            'name': 'Test Sale Order',
            'partner_id': self.env['res.partner'].create({'name': 'Test Partner', }).id,
        })
        test_ids_list = self.env[self.scenario.model_id.model].search([]).ids
        self.scenario.domain = "[['name', '=', 'Test Sale Order']]"
        self.assertEqual(test_so, self.scenario._apply_domain(test_ids_list))

    def test_get_printer(self):
        """
        Test for the correct get external printer
        """

        self.printer.default_printer_bin = self.printer_bin

        with self.assertRaises(UserError):
            self.scenario._get_printer()

        self.scenario.update({
            'printer_id': self.printer.id,
            'printer_bin': self.printer_bin.id,
        })
        self.assertEqual((self.printer, self.printer_bin), self.scenario._get_printer())

        self.user_rule.user_id = self.env.user
        self.scenario.report_id = self.so_report.id
        self.assertEqual((self.printer, self.printer_bin), self.scenario._get_printer())

    def test_print_reports(self):
        """
        Test for correct finding all scenarios and printing reports for each of them
        """

        company = self.env.company = self.company
        company.printnode_enabled = False

        user = self.env.user = self.user
        user.groups_id = None
        user.printnode_enabled = False

        self.assertFalse(self.scenario.print_reports('something', []))

        company.printnode_enabled = True
        user.groups_id = [(6, 0, [self.env.ref(SECURITY_GROUP).id])]
        user.printnode_enabled = True

        self.scenario.active = True
        self.scenario.report_id = self.so_report

        # Expected to call default printnode_print method
        self.scenario_action.code = 'print_document_on_sales_order'
        with self.cr.savepoint(), patch.object(type(self.printer), 'printnode_print',) \
                as mock_printnode_print:
            printed = self.scenario.print_reports(
                'print_document_on_sales_order',
                [self.sale_order.id]
            )
            self.assertTrue(printed)

            mock_printnode_print.assert_called_once_with(
                self.so_report,
                self.sale_order,
                copies=1,
                options={'bin': self.printer_bin.name},
            )

        # Expected to call a special method for printing
        self.scenario_action.code = 'print_picking_document_after_so_confirmation'
        with self.cr.savepoint(), patch.object(
                type(self.sale_order), '_scenario_print_picking_document_after_so_confirmation', ) \
                as mock_scenario_print:
            printed = self.scenario.print_reports(
                'print_picking_document_after_so_confirmation',
                [self.sale_order.id]
            )
            self.assertTrue(printed)

            mock_scenario_print.assert_called_once_with(
                scenario=self.scenario,
                report_id=self.scenario.report_id,
                printer_id=self.printer,
                number_of_copies=1,
                options={'bin': self.printer_bin.name},
            )

        # Attempt to print reports for different models
        # Expected to call a special method for printing
        self.scenario_action.model_id = self.env['ir.model'].search([
            ('model', '=', 'stock.picking'),
        ])
        self.scenario_action.code = 'print_product_labels_on_transfer'
        self.scenario.report_id = self.picking_report
        self.user_rule.report_id = self.picking_report

        with self.cr.savepoint(), patch.object(
                type(self.stock_picking),
                '_scenario_print_product_labels_on_transfer', ) \
                as mock_scenario_print:
            printed = self.scenario.print_reports(
                'print_product_labels_on_transfer',
                [self.stock_picking.id]
            )
            self.assertTrue(printed)

            mock_scenario_print.assert_called_once_with(
                scenario=self.scenario,
                report_id=self.scenario.report_id,
                printer_id=self.printer,
                number_of_copies=1,
                options={'bin': self.printer_bin.name},
            )

    def test_print_scenarios(self):
        """
        Test for correct finding all scenarios for current model and printing reports.
        Test print_scenarios method from PrintNodeScenarioMixin
        """

        # Expect return True
        mock_print_reports = self._create_patch_object(type(self.scenario), 'print_reports')
        mock_print_reports.return_value = True

        self.assertTrue(self.sale_order.print_scenarios('print_something'))

        mock_print_reports.assert_called_once_with(
            action='print_something',
            ids_list=[self.sale_order.id],
        )

        # Expect return UserError
        mock_print_reports.side_effect = UserError('UserError')
        pr_call_args = call(action='print_something', ids_list=[self.sale_order.id])

        with self.assertRaises(UserError) as err, self.cr.savepoint():
            self.assertIsNone(self.sale_order.print_scenarios('print_something', ))

        self.assertEqual(mock_print_reports.call_args_list, [pr_call_args, pr_call_args])
        self.assertTrue('UserError' in err.exception.args[0])

        # Expect return False
        self.assertFalse(self.sale_order.with_context(printnode_from_cron=True).print_scenarios(
            'print_something',
        ))

        self.assertEqual(
            mock_print_reports.call_args_list,
            [pr_call_args, pr_call_args, pr_call_args]
        )
