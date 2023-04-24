# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _


class GoflowSyncIndex(models.Model):

    _name = 'goflow.sync.index'

    name = fields.Char('name')
    sync_date = fields.Datetime('Sync Date', default=lambda self: fields.Datetime.now())
    order_ids = fields.Many2many(
        'sale.order', string='HR Departments',
        help='Automatically subscribe members of those departments to the channel.')
    synced_orders = fields.Boolean(default=False)
    synced_transfers = fields.Boolean(default=False)
    synced_shipped = fields.Boolean(default=False)
