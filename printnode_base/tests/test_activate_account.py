# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from unittest.mock import call

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestPrintNodeCommon


DPC_RESPONSE = {
    'data': {'is_active': True},
    'message': 'API Key successfully activated',
    'status_code': 200,
}


@tagged('post_install', '-at_install', 'pn_activate_account')  # can be run by test-tag
class TestPrintNodeAccountActivation(TestPrintNodeCommon):
    """
    Account activation tests without calls to real APIs.
    All calls to real APIs are intercepted.
    This does not test 'https://print.api<.dev>.ventor.tech' and 'https://api.printnode.com/'
    apis for stability! Should be provided other tools for API testing.
    If the api fails - this test case won't determine it.
    """

    def setUp(self):
        super(TestPrintNodeAccountActivation, self).setUp()

        # Get data for dpc_request_params from database
        self.env.cr.execute(
            "SELECT LEFT(latest_version ,2) FROM ir_module_module WHERE name=\'base\'"
        )
        odoo_version = self.env.cr.fetchone()

        self.env.cr.execute(
            "SELECT value FROM ir_config_parameter WHERE key=\'database.uuid\'"
        )
        identifier = self.env.cr.fetchone()

        self.dpc_request_params = {
            'type': 'odoo',
            'version': odoo_version[0],
            'identifier': identifier[0],
            'action': 'activate'
        }
        self.call_args = call(
            'PUT',
            f'api-key-activations/{self.account.api_key}',
            json=self.dpc_request_params
        )

        # Create Mock objects
        self.mock_send_dpc_request = self._create_patch_object(
            type(self.account),
            '_send_dpc_request'
        )
        self.mock_is_correct_dpc_api_key = self._create_patch_object(
            type(self.account),
            '_is_correct_dpc_api_key'
        )
        self.mock_update_account_limits = self._create_patch_object(
            type(self.account),
            'update_limits_for_account'
        )
        self.mock_import_devices = self._create_patch_object(type(self.account), 'import_devices')
        self.mock_unlink_devices = self._create_patch_object(type(self.account), 'unlink_devices')

    def test_account_activation_case_1(self):
        """
        Emulated state: DPC API is not responding or something went wrong.
        Expected return None.
        But will run _is_correct_dpc_api_key, update_limits_for_account, import_devices methods
        for check the correctness of the api-key and update the print limits (if possible)
        via api.printnode.com
        """

        self.mock_is_correct_dpc_api_key.return_value = True
        self.mock_send_dpc_request.return_value = None

        self.assertIsNone(self.account.activate_account())

        self.assertFalse(self.account.is_dpc_account)
        self.assertEqual(
            self.mock_send_dpc_request.call_args_list,
            [self.call_args, ],
        )
        self.mock_unlink_devices.assert_called_once()
        self.mock_is_correct_dpc_api_key.assert_called_once()
        self.mock_update_account_limits.assert_called_once()
        self.mock_import_devices.assert_called_once()

    def test_account_activation_case_2(self):
        """
        Emulated state: DPC API is not responding or something went wrong.
        Expected UserError because response is None and 'is_dpc_account' field is False.
        Will run _is_correct_dpc_api_key method for check the correctness of the api-key
        via api.printnode.com
        """

        self.mock_is_correct_dpc_api_key.return_value = False
        self.mock_send_dpc_request.return_value = None
        self.account.status = 'TestUserError'  # for UserError message test

        with self.cr.savepoint(), self.assertRaises(UserError) as err:
            self.assertIsNone(self.account.activate_account())

        self.assertTrue('TestUserError' in err.exception.args[0])
        self.assertFalse(self.account.is_dpc_account)
        self.assertEqual(
            self.mock_send_dpc_request.call_args_list,
            [self.call_args, ],
        )
        self.mock_unlink_devices.assert_called_once()
        self.mock_is_correct_dpc_api_key.assert_called_once()

    def test_account_activation_case_3(self):
        """
        Emulated state: Everything is okay - the key is from DPC
        Expected return None, 'is_dpc_account' field set to True
        Will run update_limits_for_account and import_devices methods
        for check the correctness of the api-key and update the print limits (if possible)
        via api.printnode.com
        """

        self.mock_send_dpc_request.return_value = DPC_RESPONSE

        self.assertIsNone(self.account.activate_account())

        self.assertTrue(self.account.is_dpc_account)
        self.assertEqual(
            self.mock_send_dpc_request.call_args_list,
            [self.call_args, ]
        )
        self.mock_unlink_devices.assert_called_once()
        self.mock_update_account_limits.assert_called_once()
        self.mock_import_devices.assert_called_once()

    def test_account_activation_case_4(self):
        """
        Emulated state: Status 404
        Expected return None, 'is_dpc_account' field set to False
        But will run _is_correct_dpc_api_key, update_limits_for_account, import_devices methods
        for check the correctness of the api-key and update the print limits (if possible)
        via api.printnode.com
        """

        DPC_RESPONSE.update({'status_code': 404})
        self.mock_send_dpc_request.return_value = DPC_RESPONSE
        self.mock_is_correct_dpc_api_key.return_value = True

        self.assertIsNone(self.account.activate_account())

        self.assertFalse(self.account.is_dpc_account)
        self.assertEqual(
            self.mock_send_dpc_request.call_args_list,
            [self.call_args, ]
        )
        self.mock_unlink_devices.assert_called_once()
        self.mock_is_correct_dpc_api_key.assert_called_once()
        self.mock_update_account_limits.assert_called_once()
        self.mock_import_devices.assert_called_once()

    def test_account_activation_case_5(self):
        """
        Emulated state: Something is wrong with the key
        Expected UserError
        Will run self.env.cr.commit()
        """

        DPC_RESPONSE.update({'status_code': 400, 'message': 'TestUserError_2'})
        self.mock_send_dpc_request.return_value = DPC_RESPONSE
        self.mock_is_correct_dpc_api_key.return_value = True
        self.account.status = ''  # for UserError message test
        mock_commit = self._create_patch_object(type(self.env.cr), 'commit')

        with self.cr.savepoint(), self.assertRaises(UserError) as err:
            self.assertIsNone(self.account.activate_account())

        self.assertTrue('TestUserError_2' in err.exception.args[0])
        self.assertEqual(
            self.mock_send_dpc_request.call_args_list,
            [self.call_args, ]
        )
        self.mock_unlink_devices.assert_called_once()
        mock_commit.assert_called_once()
