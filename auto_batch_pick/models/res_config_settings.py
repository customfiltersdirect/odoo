# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_batch_orders = fields.Integer(config_parameter='auto_batch_pick.auto_batch_orders',string = 'Auto Batch after ', help='Orders to be completed before auto batch is initiated', copy=True, default=25, store=True)
