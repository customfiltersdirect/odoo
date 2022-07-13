# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import UserError
import requests
from odoo.http import request
from .res_config_settings import BearerAuth
from datetime import datetime
from dateutil.tz import tzutc
import dateutil.parser


class goflow_product_tag(models.Model):
    _name = 'goflow.product.tag'

    name = fields.Char('Name')
    goflow_id = fields.Char('Goflow ID')
    color = fields.Char('Color')
    sync_products = fields.Boolean('Sync Products',default=True)

    def sync_product_tag_goflow(self):
        goflow_token = self.env['ir.config_parameter'].get_param('delivery_goflow.token_goflow')
        goflow_subdomain = self.env['ir.config_parameter'].get_param('delivery_goflow.subdomain_goflow')

        url = 'https://%s.api.goflow.com/v1/tags/products' % goflow_subdomain
        headers = {
            'X-Beta-Contact': self.env.user.partner_id.email
        }

        result = requests.get(url, auth=BearerAuth(goflow_token), headers=headers)
        goflow_api = result.json()
        tags = goflow_api


        for tag in tags:
            goflow_tag_id = tag["id"]
            goflow_tag_obj = self.env['goflow.product.tag'].search([('goflow_id', '=', goflow_tag_id)])
            if not goflow_tag_obj:
                goflow_tag_name = tag["name"]
                goflow_tag_color = tag["color"]

                self.env['goflow.product.tag'].create(
                    {'name': goflow_tag_name, 'goflow_id': goflow_tag_id, 'color': goflow_tag_color})

