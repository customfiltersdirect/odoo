# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

import base64
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestPrintNodeCommon


@tagged('post_install', '-at_install', 'pn_ir_attachment')  # can be run by test-tag
class TestPrintNodeIrAttachment(TestPrintNodeCommon):
    """
    Tests of IrAttachment model methods
    """

    def setUp(self):
        super(TestPrintNodeIrAttachment, self).setUp()

        self.attachment = self.env['ir.attachment'].create({
            'datas': base64.b64encode(b'Test content\n'),
            'name': 'Test_attachment_1',
            'type': 'binary',
            'mimetype': 'text/plain',
        })

        self.call_params = {
            "title": self.attachment.name,
            "type": "qweb-text",
            "options": {},
        }

    def test_dpc_print(self):
        """
        Test sending attachments to printer
        """

        # No printers set so UserError expected
        self.env.user.printnode_printer = None
        self.env.company.printnode_printer = None
        with self.assertRaises(UserError):
            self.attachment.dpc_print()

        # Printnode_print_b64() call expected
        self.env.user.printnode_printer = self.printer
        with self.cr.savepoint(), patch.object(type(self.printer), 'printnode_print_b64') \
                as mock_printnode_print_b64:
            mock_printnode_print_b64.return_value = 1
            message, job_ids = self.attachment.dpc_print()
            self.assertEqual(job_ids[0], 1)
            self.assertTrue('Test_attachment_1' in message)
            mock_printnode_print_b64.assert_called_once_with(
                self.attachment.datas.decode("ascii"),
                self.call_params,
                check_printer_format=False
            )

    def test_remote_dpc_print(self):
        """
        Test remote_dpc_print method from printnode_ir_attachment model
        """

        # Expected message: 'Success'
        with self.cr.savepoint(), patch.object(type(self.attachment), 'dpc_print') \
                as mock_dpc_print:
            mock_dpc_print.return_value = 'Success', 1
            res = self.attachment.remote_dpc_print()
            self.assertEqual({"status": True, "job_ids": 1, "message": 'Success'}, res)

        # Expected message: 'UserError'
        with self.cr.savepoint(), patch.object(type(self.attachment), 'dpc_print') \
                as mock_dpc_print:
            mock_dpc_print.side_effect = UserError('UserError')
            res = self.attachment.remote_dpc_print()
            self.assertEqual({"status": False, "job_ids": [], "message": 'UserError'}, res)
