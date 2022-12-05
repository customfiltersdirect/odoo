# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    goflow_pick_list_number = fields.Char('Goflow Pick List Number')
