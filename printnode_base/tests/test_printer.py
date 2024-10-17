# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

import base64
import requests
from unittest.mock import patch, call

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestPrintNodeCommon


PRINTNODE_JOB_DATA = {'title': 'TEST_S00001_1'}
ASCII_DATA = base64.b64encode(b'test content').decode('ascii')


@tagged('post_install', '-at_install', 'pn_printer')  # can be run by test-tag
class TestPrintNodePrinter(TestPrintNodeCommon):
    """
    Tests of Printer model methods
    """

    def setUp(self):
        super(TestPrintNodePrinter, self).setUp()

        self.test_partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test.partner@example.com',
        })
        self.test_sale_order = self.env['sale.order'].create({
            'name': 'Test SO',
            'partner_id': self.test_partner.id,
            'partner_invoice_id': self.test_partner.id,
            'partner_shipping_id': self.test_partner.id,
            'printnode_printed': False,
        })

    def test_name_get(self):
        """
        Test for the correct naming of the printers
        """

        name = f'{self.printer.name} ({self.printer.computer_id.name})'
        test_composite_printer_name = [(self.printer.id, name), ]
        composite_printer_name_from_method = [(self.printer.id, self.printer.display_name), ]
        self.assertEqual(
            test_composite_printer_name,
            composite_printer_name_from_method,
            "Wrong get printer name",
        )

    def test_format_title(self):
        """
        Test for the correct formatting of the title of printers in reports
        """

        objects = self.report
        test_str1 = f'{objects.display_name}_1'
        title_str = self.printer._format_title(objects, 1)
        self.assertEqual(test_str1, title_str, "Wrong make title string")

        objects += objects
        test_str2 = f'{objects._description}_2_1'
        title_str = self.printer._format_title(objects, 1)
        self.assertEqual(test_str2, title_str, "Wrong make title string")

    def test_compute_print_rules(self):
        """
        Test for the correct compute print rules
        """

        printer = self.printer
        self.assertTrue(printer.error)
        self.assertTrue('fa-exclamation-circle' in printer.notes)

        self.env.company.printnode_enabled = True
        printer._compute_print_rules()
        self.assertFalse(printer.error)
        self.assertTrue('fa-circle-o' in printer.notes)

    def test_get_source_name(self):
        """
        Test for the correct composition source name with correct latest version
        """
        module = self.env['ir.module.module'].search([('name', '=', 'printnode_base')])
        module.latest_version = '16.0.5.5.5'

        self.assertEqual(self.printer._get_source_name(), 'Odoo Direct Print PRO 5.5.5')

    def test_post_printnode_job(self):
        """
        This is a case for testing the logic of the _post_printnode_job method from
        the printnode_printer model.
        This does not test api('https://api.printnode.com/') for stability!
        Should be provided other tools for API testing. If the api fails - this test case won't
        determine it.
        """

        auth = requests.auth.HTTPBasicAuth(
            self.printer.account_id.api_key,
            self.printer.account_id.password or ''
        )

        resp = requests.Response()
        resp.__dict__.update({
            'apparent_encoding': 'ascii',
            'ok': True,
            'reason': 'Created',
            'status_code': 201,
            '_content': b'1111111111\n',
        })

        self.assertEqual(self.env['printnode.printjob'].search_count([]), 0)

        # Status_code - 201
        # Expect creating printjob
        mock_requests_post = self._create_patch_object(requests, 'post')
        mock_requests_post.return_value = resp

        job_id = self.printer._post_printnode_job(PRINTNODE_JOB_DATA)

        self.assertTrue(job_id)
        mock_requests_post.assert_called_once_with(
            'https://api.printnode.com/printjobs',
            auth=auth,
            json=PRINTNODE_JOB_DATA
        )
        self.assertEqual(self.env['printnode.printjob'].search([
            ('printnode_id', '=', job_id)
        ]).description, PRINTNODE_JOB_DATA['title'])

        # Status_code is not 201 but Content-Type is 'application/json'
        # Expect UserError with message from resp
        resp.__dict__.update({
            'headers': {'Content-Type': 'application/json'},
            'reason': 'Accepted',
            'status_code': 202,
            '_content': b'{"message":"ERROR"}\n',
        })

        mock_requests_post.return_value = resp
        job_id = None
        call_args = call(
            'https://api.printnode.com/printjobs',
            auth=auth,
            json=PRINTNODE_JOB_DATA
        )
        with self.cr.savepoint(), self.assertRaises(UserError) as err:
            job_id = self.printer._post_printnode_job(PRINTNODE_JOB_DATA)

        self.assertIsNone(job_id)
        mock_requests_post.call_args_list = [call_args, call_args]
        self.assertTrue('ERROR' in err.exception.args[0])

        # Status_code is not 201 and Content-Type is not 'application/json'
        # Expect UserError with custom message without message from resp
        resp.__dict__.update({
            'headers': {'Content-Type': 'text/html'},
        })
        mock_requests_post.return_value = resp

        with self.cr.savepoint(), self.assertRaises(UserError) as err:
            job_id = self.printer._post_printnode_job(PRINTNODE_JOB_DATA)

        self.assertIsNone(job_id)
        mock_requests_post.call_args_list = [call_args, call_args, call_args]
        self.assertFalse('ERROR' in err.exception.args[0])

    def test_printnode_print_b64(self):
        """
        This is a case for testing the logic of the printnode_print_b64 method from
        the printnode_printer model without running _post_printnode_job and
        printnode_check methods
        """

        params = {}
        print_b64_data = {
            'printerId': 0,
            'qty': 1,
            'title': None,
            'source': self.printer._get_source_name(),
            'contentType': 'raw_base64',
            'content': ASCII_DATA,
            'options': params,
        }

        # Printnode_check returned None
        # Expect called _post_printnode_job method
        mock_printnode_job = self._create_patch_object(type(self.printer), '_post_printnode_job')
        mock_printnode_check = self._create_patch_object(type(self.printer), 'printnode_check')
        mock_printnode_check.return_value = None

        self.printer.printnode_print_b64(ASCII_DATA, params)

        self.assertEqual(mock_printnode_check.call_args_list, [call(report=params)])
        mock_printnode_job.assert_called_once_with(print_b64_data)

        # Printnode_check returned an error
        # Expect UserError
        params.update({'set_error': 'testError'})
        mock_printnode_check.return_value = 'Test_Error'

        with self.cr.savepoint(), self.assertRaises(UserError) as err:
            self.printer.printnode_print_b64(ASCII_DATA, params)

        mock_printnode_job.assert_called_once()
        self.assertEqual(mock_printnode_check.call_count, 2)
        self.assertEqual('Test_Error', err.exception.args[0])

    def test_printnode_print(self):
        """
        This is a case for testing the logic of the printnode_print method from
        the printnode_printer model without running _post_printnode_job, printnode_check_report
        and printnode_check methods
        """

        ids = self.test_sale_order.mapped('id')
        content, content_type = self.so_report._render(
            report_ref=self.so_report.xml_id, res_ids=ids, data=None)

        params = {}
        print_data = {
            'printerId': 0,
            'title': 'Test SO_1',
            'source': self.printer._get_source_name(),
            'contentType': 'pdf_base64',
            'content': base64.b64encode(content).decode('ascii'),
            'qty': 1,
            'options': params,
        }

        with self.cr.savepoint(), patch.object(type(self.printer), '_post_printnode_job') \
                as mock_printnode_job, patch.object(type(self.printer), 'printnode_check_report') \
                as mock_printnode_check_report:
            mock_printnode_check_report.return_value = None

            self.printer.printnode_print(self.so_report, self.test_sale_order)

            mock_printnode_check_report.assert_called_once_with(self.so_report)
            mock_printnode_job.assert_called_once_with(print_data)

        self.assertTrue(self.test_sale_order.printnode_printed)
