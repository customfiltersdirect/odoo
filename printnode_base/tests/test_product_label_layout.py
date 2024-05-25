# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from random import randint

from odoo.tests import tagged, Form
from .common import TestPrintNodeCommon


@tagged('post_install', '-at_install', 'pn_label_layout')  # can be run by test-tag
class TestProductLabelLayout(TestPrintNodeCommon):

    def setUp(self):
        super(TestProductLabelLayout, self).setUp()
        self.company.printnode_enabled = True

    def test_open_product_product_multi_printing_wizard(self):
        """
        Test creating product_multi_printing_wizard
        """

        self.env.user.printnode_printer = self.printer

        prods = self.env['product.product'].create([
            {'name': 'product_variant_1'},
            {'name': 'product_variant_2'}
        ])
        action = prods.action_open_label_layout()
        ctx = action['context'].copy()
        ctx['active_model'] = 'product.product'
        form_wizard = Form(self.env['product.label.layout'].with_context(**ctx))
        wiz = form_wizard.save()
        self.assertEqual(self.env.user.printnode_printer.id, wiz.printer_id.id)
        self.assertEqual(wiz.product_line_ids.mapped('product_id'), prods)

    def test_open_product_template_multi_printing_wizard(self):
        """
        Test creating product_template_multi_printing_wizard
        """

        self.env.user.printnode_printer = self.printer

        prods = self.env['product.product'].create([
            {'name': 'product_tmpl_1'},
            {'name': 'product_tmpl_2'}
        ])
        templs = prods.mapped('product_tmpl_id')
        action = templs.action_open_label_layout()
        ctx = action['context'].copy()
        ctx['active_model'] = 'product.template'
        form_wizard = Form(self.env['product.label.layout'].with_context(**ctx))
        wiz = form_wizard.save()

        self.assertEqual(self.env.user.printnode_printer.id, wiz.printer_id.id)
        self.assertEqual(wiz.product_line_ids.mapped('product_tmpl_id'), templs)

    def test_open_stock_picking_multi_printing_wizard(self):
        """
        Test creating stock_picking_multi_printing_wizard
        """

        products = []
        total_qty = 0
        self.env.user.printnode_printer = self.printer

        for i in range(1, 6):
            product = self.env['product.product'].create({
                'name': f'product_{i}',
                'type': 'product',
            })
            qty = randint(1, 5)
            total_qty += qty
            products.append((product, qty))

        self.sale_order.update({
            'order_line':
            [(0, 0, {'product_id': prod.id, 'product_uom_qty': qty}) for prod, qty in products],
        })
        self.sale_order.action_confirm()

        wh_out = self.sale_order.picking_ids[:1]
        action = wh_out.action_open_label_layout()
        ctx = action['context'].copy()
        form_wizard = Form(self.env['product.label.layout'].with_context(**ctx))
        wiz = form_wizard.save()
        self.assertEqual(wiz.move_quantity, 'move')
        self.assertEqual(self.env.user.printnode_printer.id, wiz.printer_id.id)
        self.assertEqual(
            sorted(wiz.product_line_ids.mapped('product_id.id')),
            sorted([p.id for p, q in products]),
        )
