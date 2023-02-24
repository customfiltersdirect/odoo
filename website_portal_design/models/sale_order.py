# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _set_default_shipping(self):
    	if self.partner_id and self.partner_id.default_shipping_id:
    		self.partner_shipping_id = self.partner_id.default_shipping_id.id
    	return True

    @api.model
    def create(self,vals):
    	res = super(SaleOrder,self).create(vals)
    	res._set_default_shipping()
    	return res