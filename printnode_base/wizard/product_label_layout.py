# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class ProductLabelLayout(models.TransientModel):
    _name = 'product.label.layout'
    _inherit = ['product.label.layout', 'printnode.label.layout.mixin']

    move_quantity = fields.Selection(
        selection_add=[('custom_per_product', 'Custom Per Product')],
        ondelete={'custom_per_product': 'set default'}
    )

    product_line_ids = fields.One2many(
        comodel_name='product.label.layout.line',
        inverse_name='wizard_id',
        string='Products',
    )
    product_tmpl_line_ids = fields.One2many(
        comodel_name='product.label.layout.line',
        inverse_name='wizard_id',
        string='Products (Templates)',
    )

    active_model = fields.Char(
        string='Active Model'
    )

    @api.model
    def default_get(self, fields_list):
        default_vals = super(ProductLabelLayout, self).default_get(fields_list)

        if default_vals.get('move_quantity') == 'picking':
            move_line_ids = self.env.context.get('default_move_line_ids')
            product_ids = self.env.context.get('default_product_ids', [])
            qties = defaultdict(int, {k: 0 for k in product_ids})

            if move_line_ids:
                uom_unit = self.env.ref('uom.product_uom_categ_unit', raise_if_not_found=False)
                for line in self.env['stock.move.line'].browse(move_line_ids):
                    if line.product_uom_id.category_id == uom_unit:
                        qties[line.product_id.id] += line.quantity

            default_vals.update({
                'active_model': 'product.product',
                'product_line_ids': [
                    (0, 0, {'product_id': p, 'quantity': int(q)})
                    for p, q in qties.items()
                ],
            })
        elif self.env.context.get('default_product_tmpl_ids'):
            product_tmpl_ids = self.env.context.get('default_product_tmpl_ids')

            default_vals.update({
                'active_model': 'product.template',
                'product_tmpl_line_ids': [
                    (0, 0, {'product_tmpl_id': p_id, 'quantity': 1})
                    for p_id in product_tmpl_ids
                ]
            })
        else:
            product_ids = self.env.context.get('default_product_ids', [])

            default_vals.update({
                'active_model': 'product.product',
                'product_line_ids': [
                    (0, 0, {'product_id': p_id, 'quantity': 1})
                    for p_id in product_ids
                ],
            })

        return default_vals

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super().fields_get(allfields=allfields, attributes=attributes)

        # TODO: Remove "Operation Quantities" from list of values - for now it doesn't work
        # Remove "Operation Quantities" from list of values
        # if 'move_quantity' in fields:
        #     if self.env.context.get('default_move_quantity') != 'move':
        #         fields['move_quantity'].update({
        #             'selection': [
        #                 ('custom', 'Custom'),
        #                 ('custom_per_product', 'Custom Per Product')
        #             ]
        #         })
        return fields

    def _prepare_report_data(self):
        xml_id, data = super()._prepare_report_data()

        if (
            self._origin  # Not raise error on the first call
            and self.move_quantity == 'move'
            and not self.move_ids
            and (self.product_line_ids or self.product_tmpl_line_ids)
        ):
            # Most likely we are printing labels from product form view
            # In this case this value is not valid
            # TODO: Check fields_get for the better solution
            raise UserError(_('You can use "Operation Quantities" only when printing from picking'))

        if self.move_quantity != 'custom_per_product':
            return xml_id, data

        if self.active_model == 'product.template' and self.product_tmpl_line_ids:
            data['quantity_by_product'] = {
                str(line.product_tmpl_id.id): line.quantity for line in self.product_tmpl_line_ids
            }
        elif self.active_model == 'product.product' and self.product_line_ids:
            data['quantity_by_product'] = {
                str(line.product_id.id): line.quantity for line in self.product_line_ids
            }
        return xml_id, data

    def process(self):
        self.ensure_one()

        if self.move_quantity == 'custom_per_product':
            self._check_quantity()

        # Download PDF if no printer selected
        if not self.printer_id:
            # Update context to download on client side instead of printing
            # Check action_service.js file for details
            return super(ProductLabelLayout, self.with_context(download_only=True)).process()

        xml_id, data = self._prepare_report_data()

        if not xml_id:
            raise UserError(_('Unable to find report template for %s format', self.print_format))

        return self.env.ref(xml_id).with_context(
            printer_id=self.printer_id.id,
            printer_bin=self.printer_bin.id
        ).report_action(None, data=data)

    def _check_quantity(self):
        for rec in self.product_line_ids:
            if rec.quantity < 1:
                raise ValidationError(
                    _(
                        'Quantity can not be less than 1 for product {product}'
                    ).format(**{
                        'product': rec.product_id.display_name or rec.product_tmpl_id.display_name,
                    })
                )


class ProductLabelLayoutLine(models.TransientModel):
    _name = 'product.label.layout.line'
    _description = 'Choose the sheet layout to print the labels / Line'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product (Template)',
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )

    quantity = fields.Integer(
        required=True,
        default=1,
    )

    wizard_id = fields.Many2one(
        comodel_name='product.label.layout',
    )
