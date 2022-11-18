# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class GroupMoveLine(models.Model):
    _name = 'group.move.line'

    product_id = fields.Many2one('product.product', 'Product', ondelete="cascade", check_company=True,
                                 domain="[('type', '!=', 'service'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 index=True)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', required=True,
                                     domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_qty = fields.Float(
        'Real Reserved Quantity', digits=0, copy=False)
    product_uom_qty = fields.Float(
        'Reserved', default=0.0, digits='Product Unit of Measure', required=True, copy=False)
    qty_done = fields.Float('Done', default=0.0, digits='Product Unit of Measure', copy=False)
    location_id = fields.Many2one('stock.location', 'From', domain="[('usage', '!=', 'view')]", check_company=True,
                                  required=True)
    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')], string='Status',
        copy=False, default='draft', index=True, readonly=True)
    location_dest_id = fields.Many2one('stock.location', 'To', domain="[('usage', '!=', 'view')]", check_company=True,
                                       required=True)
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number',
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]", check_company=True)
    lot_name = fields.Char('Lot/Serial Number Name')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True, index=True)
    batch_id = fields.Many2one('stock.picking.batch')
