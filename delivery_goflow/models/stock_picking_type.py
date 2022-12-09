# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import UserError
import requests
from odoo.http import request
from .res_config_settings import BearerAuth


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_creating_batch = fields.Boolean('Create Batches')
