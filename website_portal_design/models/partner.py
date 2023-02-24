# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class Partner(models.Model):
    _inherit = "res.partner"

    default_shipping_id = fields.Many2one('res.partner',string="Default Shipping")
    is_removed = fields.Boolean(string="Removed")

