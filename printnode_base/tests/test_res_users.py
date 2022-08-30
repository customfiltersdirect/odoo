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

        self.printnode_workstation_label_printer = self.env['printnode.printer'].create({
            'name': 'Printnode Workstation Label Printer',
            'status': 'online',
            'computer_id': self.computer.id,
        })

    def test_get_shipping_label_printer(self):
        """
        Test for the correct selection of Shipping Label Printer
        """
        user = self.env.user
        company = self.env.company

        # Test Case - 1
        # No printer is assigned
        # 1.1 Expected to raise UserError with raise_exc=True
        with self.assertRaises(UserError):
            self.user.get_shipping_label_printer(raise_exc=True)

        # 1.2 Expected to return None without raise_exc=True
        self.assertFalse(self.user.get_shipping_label_printer())

        # Test Case - 2
        # Only Company Label Printer is defined
        # It is expected to be selected
        company.company_label_printer = self.company_printer

        printer = user.get_shipping_label_printer(self.delivery_carrier)
        self.assertEqual(printer, company.company_label_printer)

        # Test Case - 3
        # Company Label Printer is defined
        # Delivery Carrier Printer is defined
        # Delivery Carrier Printer is expected to be selected
        self.delivery_carrier.printer_id = self.printer.id

        # The carrier_id parameter was not passed
        printer = user.get_shipping_label_printer()
        self.assertNotEqual(printer, self.delivery_carrier.printer_id)

        # The carrier_id parameter must be passed
        printer = user.get_shipping_label_printer(self.delivery_carrier)
        self.assertEqual(printer, self.delivery_carrier.printer_id)
        self.assertIsNotNone(company.company_label_printer.id)

        # Test Case - 4
        # Company Label Printer is defined
        # Delivery Carrier Printer is defined
        # Shipping Label Printer for current user is defined
        # Shipping Label Printer for current user is expected to be selected
        user.user_label_printer = self.user_printer.id

        printer = user.get_shipping_label_printer(self.delivery_carrier)
        self.assertEqual(printer, user.user_label_printer)
        self.assertIsNotNone(company.company_label_printer.id)
        self.assertIsNotNone(self.delivery_carrier.printer_id.id)

        # Test Case - 5
        # All printers are defined
        # The Workstation Label Printer is expected to be selected
        new_context = self.env.context.copy()
        workstation_devices = {
            'printnode_workstation_label_printer_id': self.printnode_workstation_label_printer.id
        }
        new_context.update(workstation_devices)

        printer = user.with_context(new_context).get_shipping_label_printer(
            self.delivery_carrier)
        self.assertEqual(printer, self.printnode_workstation_label_printer)
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

    def test_get_printer_within_report_download(self):
        """
        Test for the correct get printer within report download
        """

        company_printer = self.company_printer
        user_printer = self.user_printer

        self.company.write({'printnode_printer': company_printer.id})
        self.user.write({'printnode_printer': user_printer.id})

        # Expected UserRule Printer
        self.action_button.write({'printer_id': False})
        printer, printer_bin = self.user.get_report_printer(self.so_report.id)
        self.assertEqual(printer.id, self.user_rule.printer_id.id)

        # Expected User's Printer
        self.user_rule.write({'report_id': self.delivery_slip_report.id})
        printer, printer_bin = self.user.get_report_printer(self.so_report.id)
        self.assertEqual(printer.id, self.user.printnode_printer.id)

        # Expected Company's Printer
        self.user.write({'printnode_printer': False})
        printer, printer_bin = self.user.get_report_printer(self.so_report.id)
        self.assertEqual(printer.id, self.company.printnode_printer.id)

        # Expected Workstation Printer
        new_ctx = self.env.context.copy()
        new_ctx.update({
            'printnode_workstation_printer_id': self.printnode_workstation_label_printer.id
        })

        printer, printer_bin = self.user.with_context(new_ctx).get_report_printer(
            self.so_report.id
        )
        self.assertEqual(printer, self.printnode_workstation_label_printer)

    def test_get_workstation_device(self):
        """
        Test for helper method to setting device for current workstation
        """

        self.assertIsNone(self.user._get_workstation_device('something'))

        self.assertIsNone(self.user.with_context({
            'printnode_workstation_printer_id': 'lalala'
        })._get_workstation_device('printnode_workstation_printer_id'))

        # Workstation_printer
        self.assertEqual(self.user.with_context({
            'printnode_workstation_printer_id': self.printer.id
        })._get_workstation_device('printnode_workstation_printer_id'), self.printer)

        # Workstation_scales
        self.assertEqual(self.user.with_context({
            'printnode_workstation_scales_id': self.scales.id
        })._get_workstation_device('printnode_workstation_scales_id'), self.scales)

    def test_validate_device_id(self):
        """
        Test for correct validate device id
        """

        devices = {
            'printnode_workstation_printer_id': self.printer.id,
            'printnode_workstation_label_printer_id': self.printer.id,
            'printnode_workstation_scales_id': self.scales.id,
        }

        device_names = self.user.validate_device_id(devices)

        self.assertEqual(device_names['printnode_workstation_printer_id'], self.printer.name)
        self.assertEqual(device_names['printnode_workstation_label_printer_id'], self.printer.name)
        self.assertEqual(device_names['printnode_workstation_scales_id'], self.scales.name)
