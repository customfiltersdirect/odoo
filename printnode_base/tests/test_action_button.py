# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestPrintNodeCommon


@tagged('post_install', '-at_install', 'pn_action_button')  # can be run by test-tag
class TestPrintNodeActionButton(TestPrintNodeCommon):
    """
    Tests of ActionButton model methods
    """

    def setUp(self):
        super(TestPrintNodeActionButton, self).setUp()

        self.user_rule.update({'report_id': self.report.id})

    def test_check_number_of_copies(self):
        """
        Test copy limit > 1
        """

        with self.assertRaises(UserError):
            self.action_button.number_of_copies = 0

    def test_action_domain(self):
        """
        Test _get_model_objects method from printnode.action.button model
        """

        partner_1 = self.env['res.partner'].create({'name': 'Direct Print Partner1'})
        partner_2 = self.env['res.partner'].create({'name': 'Direct Print Partner2'})
        sl_order = self.env['sale.order'].create({'partner_id': partner_1.id})

        # Empty ids_list
        related_model = self.action_button._get_model_objects([])
        self.assertEqual(self.env[self.action_button.model], related_model)

        # Empty action domain
        self.assertEqual(self.action_button.domain, '[]')
        objects = self.action_button._get_model_objects(sl_order.ids)
        self.assertEqual(objects, sl_order)

        # Set action domain for 'partner_1' (partner for 'sl_order')
        self.action_button.domain = f'[["partner_id", "=", {partner_1.id}]]'
        objects = self.action_button._get_model_objects(sl_order.ids)
        self.assertEqual(objects, sl_order)

        # Set action domain for 'partner_2'. Sale Order will be filtered.
        self.action_button.domain = f'[["partner_id", "=", {partner_2.id}]]'
        objects = self.action_button._get_model_objects(sl_order.ids)
        self.assertFalse(objects)

    def test_onchange_printer(self):
        """
        Test reset printer_bin field
        """

        self.assertNotEqual(self.action_button.printer_bin, self.printer_bin)
        self.printer.default_printer_bin = self.printer_bin.id
        self.action_button._onchange_printer()
        self.assertEqual(self.action_button.printer_bin, self.printer_bin)

    def test_get_printer_for_action_button(self):
        """
        Test for correct getting printer, printer_bin for action button
        """

        # Expected UserError
        with self.cr.savepoint(), self.assertRaises(UserError):
            self.company.write({'printnode_printer': None})
            self.user.write({'printnode_printer': None})
            self.action_button.write({'printer_id': None})
            self.user_rule.write({'printer_id': None})
            self.action_button.with_user(self.user.id)._get_action_printer()

        # SetUp
        company_printer = self.company_printer
        user_printer = self.company_printer
        action_printer = self.action_printer
        self.company.write({'printnode_printer': company_printer.id})
        self.user.write({'printnode_printer': user_printer.id})
        self.action_button.write({'printer_id': action_printer.id})

        # Expected ActionButton Printer
        printer, printer_bin = self.action_button.with_user(self.user.id)._get_action_printer()
        self.assertEqual(printer.id, action_printer.id)

        # Expected UserRule Printer
        self.action_button.write({'printer_id': False})
        printer, printer_bin = self.action_button.with_user(self.user.id)._get_action_printer()
        self.assertEqual(printer.id, self.user_rule.printer_id.id)

        # Expected User's Printer
        self.user_rule.write({'report_id': self.delivery_slip_report.id})
        printer, printer_bin = self.action_button.with_user(self.user.id)._get_action_printer()
        self.assertEqual(printer.id, self.user.printnode_printer.id)

        # Expected Company's Printer
        self.user.write({'printnode_printer': False})
        printer, printer_bin = self.action_button.with_user(self.user.id)._get_action_printer()
        self.assertEqual(printer.id, self.company.printnode_printer.id)
