# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import TestPrintNodeCommon


@tagged('post_install', '-at_install', 'pn_rule')  # can be run by test-tag
class TestPrintNodeRule(TestPrintNodeCommon):
    """
    Tests of Rule model methods
    """

    def test_compute_print_rules(self):
        """
        Test for the correct compute print rules
        """

        rule = self.user_rule
        rule.printer_id = None
        self.assertFalse(rule.error)
        self.assertTrue('Please, fill in the Report and Printer fields' in rule.notes)

        rule.printer_id = self.printer
        self.assertTrue(rule.error)
        self.assertTrue('fa-exclamation-circle' in rule.notes)

        self.env.company.printnode_enabled = True
        rule._compute_print_rules()
        self.assertFalse(rule.error)
        self.assertTrue('fa-circle-o' in rule.notes)

    def test_onchange_printer(self):
        """
        Test reset printer_bin field
        """

        self.assertNotEqual(self.user_rule.printer_bin, self.printer_bin)
        self.printer.default_printer_bin = self.printer_bin.id
        self.user_rule._onchange_printer()
        self.assertEqual(self.user_rule.printer_bin, self.printer_bin)
