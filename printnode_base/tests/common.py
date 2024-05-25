# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from unittest.mock import patch
from odoo.tests import common


SECURITY_GROUP = 'printnode_base.printnode_security_group_user'
BASE_INTERNAL_USER_GROUP = 'base.group_user'

# Devices from api.printnode
TEST_COMPUTERS_FROM_PRINTNODE = [
    {
        "hostname": "ventortech@VENTORTECH-DEV",
        "id": 413,
        "name": "VENTORTECH-DEV",
        "state": "disconnected",
    },
]
TEST_PRINTERS_FROM_PRINTNODE = [
    {
        "computer": TEST_COMPUTERS_FROM_PRINTNODE[0],
        "default": True,
        "description": "PDF",
        "id": 710,
        "name": "PDF",
        "state": 'online',
        "capabilities": {
            "bins": [
                "Auto",
                "Tray1",
                "Tray2"
            ],
        },
    },
]
TEST_SCALES_FROM_PRINTNODE = [
    {
        "computer": TEST_COMPUTERS_FROM_PRINTNODE[0],
        'productId': '730',
        'deviceName': 'Local Test Scales 2',
        'deviceNum': '2222',
    },
]


class TestPrintNodeCommon(common.TransactionCase):
    """
    Setup to be used post-install with printnode_base test configuration
    """

    def setUp(self):
        super(TestPrintNodeCommon, self).setUp()

        self.company = self.env.ref('base.main_company')

        self.user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Direct Print User',
            'company_id': self.company.id,
            'login': 'user',
            'email': 'user@print.node',
            'groups_id': [(6, 0, [
                self.env.ref(SECURITY_GROUP).id,
                self.env.ref(BASE_INTERNAL_USER_GROUP).id,
            ])]
        })

        # Models
        self.so_model = self.env['ir.model'].search([('model', '=', 'sale.order')])

        # Reports
        self.so_report = self.env['ir.actions.report'].search([
            ('name', '=', 'Quotation / Order'),
            ('model', '=', 'sale.order'),
        ], limit=1)

        self.delivery_slip_report = self.env['ir.actions.report'].search([
            ('name', '=', 'Delivery Slip'),
        ], limit=1)

        self.report = self.env['ir.actions.report'].create({
            'name': 'Model Overview',
            'model': 'ir.model',
            'report_type': 'qweb-pdf',
            'report_name': 'base.report_irmodeloverview',
        })

        # PN account
        self.account = self.env['printnode.account'].create({
            'api_key': 'apikey',
        })

        # Devices
        self.computer = self.env['printnode.computer'].create({
            'name': 'Local Computer',
            'status': 'connected',
            'account_id': self.account.id,
        })

        self.printer = self.env['printnode.printer'].create({
            'name': 'Local Printer',
            'status': 'offline',
            'computer_id': self.computer.id,
        })

        self.printer_bin = self.env['printnode.printer.bin'].create({
            'name': 'Test Bin',
            'printer_id': self.printer.id,
        })

        self.company_printer = self.env['printnode.printer'].create({
            'name': 'Company Printer',
            'status': 'online',
            'computer_id': self.computer.id,
        })

        self.user_printer = self.env['printnode.printer'].create({
            'name': 'User Printer',
            'status': 'online',
            'computer_id': self.computer.id,
        })

        self.action_printer = self.env['printnode.printer'].create({
            'name': 'Action Printer',
            'status': 'online',
            'computer_id': self.computer.id,
        })

        self.scales = self.env['printnode.scales'].create({
            'name': 'Local Scales',
            'device_num': 1,
            'printnode_id': 1,
            'status': 'offline',
            'computer_id': self.computer.id,
        })

        # Action methods
        printnode_action_method = self.env['printnode.action.method'].search([
            ('model_id', '=', self.so_model.id),
            ('method', '=', 'action_confirm'),
        ])

        self.action_method = (printnode_action_method if printnode_action_method else
                              self.env['printnode.action.method'].create({
                                  'name': 'SO Print',
                                  'model_id': self.so_model.id,
                                  'method': 'action_confirm',
                              }))

        self.action_button = self.env['printnode.action.button'].create({
            'model_id': self.so_model.id,
            'method_id': self.action_method.id,
            'description': 'Print SO by confirm button',
            'report_id': self.report.id,
            'printer_id': self.printer.id,
        })

        # Rules
        self.user_rule = self.env['printnode.rule'].create({
            'user_id': self.user.id,
            'printer_id': self.printer.id,
            'report_id': self.so_report.id,
        })

        # Scenarios
        self.scenario_action = self.env['printnode.scenario.action'].create({
            'name': "Test Printnode Scenario Action",
            'code': 'test_scenario_action',
            'model_id': self.so_model.id,
            'reports_model_id': self.so_model.id,
        })

        self.scenario = self.env['printnode.scenario'].create({
            'action': self.scenario_action.id,
            'report_id': self.so_report.id,
        })

        # Partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test.partner@example.com',
        })

        # Sale_order
        self.sale_order = self.env['sale.order'].create({
            'name': 'Test SO',
            'partner_id': self.partner.id,
            'printnode_printed': False,
        })

        # Delivery carrier
        self.delivery_carrier = self.env['delivery.carrier'].create({
            'name': 'Test Delivery Carrier',
            'product_id': self.env['product.product'].create({
                'name': 'Test Product',
                'type': 'product',
            }).id,
        })

        # Products
        self.product_id = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
        })

        # Locations
        self.location_dest = self.env['stock.location'].create({
            'name': 'Test_dest_location',
            'usage': 'customer'
        })

        # Picking type
        self.picking_type_incoming = \
            self.env['stock.picking.type'].sudo().with_context(active_test=False).search([
                ('code', '=', 'incoming'),
            ], limit=1)

        # Stock picking
        self.stock_picking = self.env['stock.picking'].create({
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.location_dest.id,
            'move_type': 'direct',
            'picking_type_id': self.picking_type_incoming.id,
            'name': "Test Stock Picking",
        })

        # Stock move
        self.stock_move = self.env['stock.move'].create({
            'name': 'Test move',
            'product_id': self.product_id.id,
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.location_dest.id,
            'product_uom': self.env.ref('uom.product_uom_unit').id,
            'product_uom_qty': 2,
            'picking_type_id': self.picking_type_incoming.id,
            'picking_id': self.stock_picking.id,
        })

    def _create_patch_object(self, target, attribute):
        """
        Improved object patcher method from
        'https://docs.python.org/3/library/unittest.mock-examples.html#nesting-patches'

        This method makes it easier to work with unittest.mock.patch()<.object()> functions.
        It avoids extra nested indentation as when using patch() with the "with" context manager.
        """

        patcher = patch.object(target, attribute)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def _create_workstation(self):
        """
        Create a test workstation and define printers and scales.
        """
        workstation_id = self.env['printnode.workstation'].create({
            'name': 'Test Workstation',
            'printer_id': self.printer.id,
            'label_printer_id': self.label_printer.id,
            'scales_id': self.scales.id,
        })

        return workstation_id
