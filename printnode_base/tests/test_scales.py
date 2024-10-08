# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from unittest.mock import patch
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestPrintNodeCommon


@tagged('post_install', '-at_install', 'pn_scales')  # can be run by test-tag
class TestPrintNodeScales(TestPrintNodeCommon):
    """
    Tests of Scales model methods
    """

    def test_name_get(self):
        """
        Test for the correct naming of the scales
        """

        name = f'{self.scales.name}-{self.scales.device_num} ({self.scales.computer_id.name})'
        test_composite_scales_name = [(self.scales.id, name), ]
        composite_scales_name_from_method = [(self.scales.id, self.scales.display_name), ]

        self.assertEqual(
            test_composite_scales_name,
            composite_scales_name_from_method,
            "Wrong get scales name",
        )

    def test_compute_scales_status(self):
        """
        Test to check the status of the computer and printer correctly
        """

        self.assertFalse(self.scales.online, "Wrong compute scales status")

        self.scales.status = 'online'
        self.assertTrue(self.scales.online, "Wrong compute scales status")

        self.computer.status = None
        self.assertFalse(self.scales.online, "Wrong compute scales status")

    def test_get_scales_measure_kg(self):
        """
        Test for the correctness of getting scales and handling exceptions
        """

        weighing_result = None
        with self.assertRaises(UserError), self.cr.savepoint(), patch.object(
                type(self.account),
                '_send_printnode_request',
                return_value=weighing_result,
        ):
            self.scales.get_scales_measure_kg()

        weighing_result = {
            'mass': [0.0, ],
        }
        with self.assertRaises(UserError), self.cr.savepoint(), patch.object(
                type(self.account),
                '_send_printnode_request',
                return_value=weighing_result,
        ):
            self.scales.get_scales_measure_kg()

        weighing_result = {
            'mass': [-1.0, ],
        }
        with self.assertRaises(UserError), self.cr.savepoint(), patch.object(
                type(self.account),
                '_send_printnode_request',
                return_value=weighing_result,
        ):
            self.scales.get_scales_measure_kg()

        weighing_result = {
            'mass': [2000000000.0, ],
        }
        with self.cr.savepoint(), patch.object(
                type(self.account),
                '_send_printnode_request',
                return_value=weighing_result,
        ):
            self.assertEqual(
                weighing_result.get('mass')[0] / 1000000000,
                self.scales.get_scales_measure_kg()
            )
