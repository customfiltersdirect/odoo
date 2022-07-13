# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import UserError
import requests
from odoo.http import request

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    goflow_token = fields.Char(config_parameter='delivery_goflow.token_goflow',string = 'Token GoFlow', help='Necessary for integrations w', copy=True, default='', store=True)
    goflow_subdomain = fields.Char(config_parameter='delivery_goflow.subdomain_goflow',string='Subdomain',help='Subdomain of Goflow account',copy=True, default='', store=True)
    @api.onchange('goflow_token','goflow_subdomain')
    def _onchange_goflow_token(self):
        if not self.goflow_token and self.goflow_subdomain:
            return
        goflow_token = self.env['ir.config_parameter'].get_param('delivery_goflow.token_goflow')
        goflow_subdomain = self.env['ir.config_parameter'].get_param('delivery_goflow.subdomain_goflow')

        if self.goflow_token == goflow_token and self.goflow_subdomain == goflow_subdomain:
            return
        url = 'https://%s.api.goflow.com/v1/inventory/adjustments'%self.goflow_subdomain
        headers = {

            'X-Beta-Contact':self.env.user.partner_id.email
        }
        try:
            result = requests.get(url, auth=BearerAuth(self.goflow_token),headers=headers)
            error_code = result.status_code
        except requests.exceptions.RequestException:
            error_code = 500
        print (error_code)
        if error_code == 200:
            return
        self.goflow_token = ''
        if error_code == 401:
            return {'warning': {'message': _('The token input/subdomain is not valid')}}
        elif error_code == 403:
            return {'warning': {'message': _('This referer is not authorized')}}
        elif error_code == 500:
            return {'warning': {'message': _('The Goflow server is unreachable')}}
