# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import UserError
import requests
from odoo.http import request
from .res_config_settings import BearerAuth

class Company(models.Model):
    _inherit = 'res.company'

    use_for_goflow_api  = fields.Boolean('Use for Goflow')