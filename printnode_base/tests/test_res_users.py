# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestPrintNodeCommon


@tagged('post_install', '-at_install', 'pn_users')  # can be run by test-tag
class TestPrintNodeUsers(TestPrintNodeCommon):
    """
    Tests of User model methods
    """

    def setUp(self):
        super(TestPrintNodeUsers, self).setUp()

        self.report_printer = self.env['printnode.printer'].create({
            'name': 'Report Printer',
            'status': 'online',
            'computer_id': self.computer.id,
        })

        self.label_printer = self.env['printnode.printer'].create({
            'name': 'Local Label Printer',
            'status': 'online',
            'computer_id': self.computer.id,
        })

        self.report_policy = self.env['printnode.report.policy'].create({
            'report_id': self.so_report.id,
            'printer_id': self.report_printer.id,
        })

    def test_get_shipping_label_printer_case_1(self):
        """
        Test Case - 1
        No printer is assigned
        """
        # 1.1 Expected to raise UserError (with raise_exc=True)
        with self.assertRaises(UserError):
            self.user.get_shipping_label_printer(raise_exc=True)

        # 1.2 Expected to return False (without raise_exc=True)
        self.assertFalse(self.user.get_shipping_label_printer())

    def test_get_shipping_label_printer_case_2(self):
        """
        Test Case - 2
        Only Company Label Printer is defined
        """
        user = self.env.user
        company = self.env.company

        # Company Label Printer is expected to be selected
        company.company_label_printer = self.company_printer

        printer = user.get_shipping_label_printer(self.delivery_carrier)
        self.assertEqual(printer, company.company_label_printer)

    def test_get_shipping_label_printer_case_3(self):
        """
        Test Case - 3
        Company Label Printer is defined
        Delivery Carrier Printer is defined
        """
        user = self.env.user
        company = self.env.company

        # Delivery Carrier Printer is expected to be selected
        self.delivery_carrier.printer_id = self.printer.id

        # The carrier_id parameter not passed
        printer = user.get_shipping_label_printer()
        self.assertNotEqual(printer, self.delivery_carrier.printer_id)

        # The carrier_id parameter must be passed
        printer = user.get_shipping_label_printer(self.delivery_carrier)
        self.assertEqual(printer, self.delivery_carrier.printer_id)
        self.assertIsNotNone(company.company_label_printer.id)

    def test_get_shipping_label_printer_case_4(self):
        """
        Test Case - 4
        Company Label Printer is defined
        Delivery Carrier Printer is not defined
        Shipping Label Printer for current user is defined
        """
        user = self.env.user
        company = self.env.company

        # Shipping Label Printer for current user is expected to be selected
        user.user_label_printer = self.user_printer.id

        printer = user.get_shipping_label_printer(self.delivery_carrier)
        self.assertEqual(printer, user.user_label_printer)
        self.assertIsNotNone(company.company_label_printer.id)
        self.assertFalse(self.delivery_carrier.printer_id.id)

    def test_get_shipping_label_printer_case_5(self):
        """
        Test Case - 5
        All printers are defined
        """
        user = self.env.user
        company = self.env.company

        # The Workstation Label Printer is expected to be selected
        workstation_id = self._create_workstation()

        printer = user.with_context(printnode_workstation_id=workstation_id.id). \
            get_shipping_label_printer(self.delivery_carrier)
        self.assertEqual(printer, self.label_printer)
        self.assertIsNotNone(company.company_label_printer.id)
        self.assertIsNotNone(self.delivery_carrier.printer_id.id)
        self.assertIsNotNone(user.user_label_printer.id)

    def test_get_scales(self):
        """
        Test for the correct assignment of scales for user
        """

        self.user.printnode_scales = self.scales
        test_scales = self.user.get_scales()
        self.assertEqual(test_scales.id, self.scales.id, "Wrong assignment of scales for user")

        self.user.printnode_scales = None
        test_scales = self.user.get_scales()
        self.assertNotEqual(test_scales.id, self.scales.id)

        self.env.company.printnode_scales = self.scales
        test_scales = self.user.with_env(self.env).get_scales()
        self.assertEqual(test_scales.id, self.scales.id, "Wrong assignment of scales for user")

    def test_printer_selection(self):
        """
        Test to check printer selection
        """

        # Set Up
        user = self.user
        company = self.env.company
        user.printnode_printer = self.user_printer
        company.printnode_printer = self.company_printer
        self.action_button.printer_id = False
        self.report_policy.printer_id = self.report_printer

        # Expected Printer from User Rules
        printer, printer_bin = user.get_report_printer(self.so_report.id)
        self.assertEqual(printer.id, self.user_rule.printer_id.id)

        # Expected Printer from Report Policy
        self.user_rule.report_id = self.delivery_slip_report.id
        printer, printer_bin = user.get_report_printer(self.so_report.id)
        self.assertEqual(printer.id, self.report_policy.printer_id.id)

        # Expected User's Printer
        self.report_policy.printer_id = False
        printer, printer_bin = user.get_report_printer(self.so_report.id)
        self.assertEqual(printer.id, user.printnode_printer.id)

        # Expected Company Printer
        self.user.printnode_printer = False
        printer, printer_bin = user.get_report_printer(self.so_report.id)
        self.assertEqual(printer.id, company.printnode_printer.id)

        # Expected Workstation Printer
        workstation_id = self._create_workstation()
        printer, printer_bin = user.with_context(
            printnode_workstation_id=workstation_id.id).get_report_printer(self.so_report.id)
        self.assertEqual(printer.id, self.printer.id)

    def test_get_workstation_device(self):
        """
        Test for helper method to setting device for current workstation
        """
        workstation_id = self._create_workstation()

        # Workstation devices will not be defined
        self.assertIsNone(self.user._get_workstation_device('printer_id'))
        self.assertIsNone(self.user._get_workstation_device('label_printer_id'))
        self.assertIsNone(self.user._get_workstation_device('scales_id'))

        # Workstation printer will be defined
        self.assertEqual(
            self.user.with_context(
                printnode_workstation_id=workstation_id.id)._get_workstation_device('printer_id'),
            self.printer,
        )

        # Workstation label_printer will be defined
        self.assertEqual(self.user.with_context(
            printnode_workstation_id=workstation_id.id)._get_workstation_device('label_printer_id'),
            self.label_printer,
        )

        # Workstation scales will be defined
        self.assertEqual(self.user.with_context(
            printnode_workstation_id=workstation_id.id)._get_workstation_device('scales_id'),
            self.scales,
        )
