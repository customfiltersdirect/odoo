# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import TestPrintNodeCommon


@tagged('post_install', '-at_install', 'pn_delivery_carrier')  # can be run by test-tag
class TestPrintNodeDeliveryCarrier(TestPrintNodeCommon):
    """
    Tests of DeliveryCarrier model methods
    """

    def test_onchange_printer(self):
        """Test reset printer_bin field
        """

        self.assertNotEqual(self.delivery_carrier.printer_bin, self.printer_bin)
        self.printer.default_printer_bin = self.printer_bin.id

        self.delivery_carrier.printer_id = self.printer.id
        self.delivery_carrier._onchange_printer()
        self.assertEqual(self.delivery_carrier.printer_bin, self.printer_bin)
