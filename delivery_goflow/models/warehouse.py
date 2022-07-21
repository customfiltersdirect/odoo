# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import UserError
import requests
from odoo.http import request
from .res_config_settings import BearerAuth

class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    goflow_id = fields.Char('Goflow ID')
    sync_orders = fields.Boolean('Sync Orders',default=False)

