# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import UserError
import requests
from odoo.http import request
from datetime import datetime

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ## new date for cut off
    goflow_cutoff_date = fields.Datetime('Cutoff Date',config_parameter='delivery_goflow.goflow_cutoff_date',help='Cut off Date')
    goflow_token = fields.Char(config_parameter='delivery_goflow.token_goflow',string = 'Token GoFlow', help='Necessary for integrations w', copy=True, default='5a07ac83f5d04ad89390da6026bf63d4', store=True)
    goflow_subdomain = fields.Char(config_parameter='delivery_goflow.subdomain_goflow',string='Subdomain',help='Subdomain of Goflow account',copy=True, default='Mervfilters', store=True)
    last_inpicking_sync = fields.Datetime(config_parameter='delivery_goflow.last_inpicking_sync')
    last_shipped_sync = fields.Datetime(config_parameter='delivery_goflow.last_shipped_sync')
    last_readytopick_sync = fields.Datetime(config_parameter='delivery_goflow.last_readytopick_sync')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        icp = self.env['ir.config_parameter'].sudo()
        last_inpicking_sync_str = icp.get_param('delivery_goflow.last_inpicking_sync')
        last_shipped_sync_str = icp.get_param('delivery_goflow.last_shipped_sync')
        last_readytopick_sync_str = icp.get_param('delivery_goflow.last_readytopick_sync')

        # Convert the string value to a datetime object
        if last_inpicking_sync_str:
            last_inpicking_sync_str = datetime.fromisoformat(last_inpicking_sync_str)
        else:
            last_inpicking_sync_str = False

        # Convert the string value to a datetime object
        if last_shipped_sync_str:
            last_shipped_sync_str = datetime.fromisoformat(last_shipped_sync_str)
        else:
            last_shipped_sync_str = False

        # Convert the string value to a datetime object
        if last_readytopick_sync_str:
            last_readytopick_sync_str = datetime.fromisoformat(last_readytopick_sync_str)
        else:
            last_readytopick_sync_str = False


        res.update(
            last_inpicking_sync=last_inpicking_sync_str,
            last_shipped_sync=last_shipped_sync_str,
            last_readytopick_sync=last_readytopick_sync_str,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        icp = self.env['ir.config_parameter'].sudo()

        # Convert the datetime object to a string value
        if self.last_inpicking_sync:
            last_inpicking_sync_str = self.last_inpicking_sync.isoformat()
        else:
            last_inpicking_sync_str = ''

        # Convert the datetime object to a string value
        if self.last_shipped_sync:
            last_shipped_sync_str = self.last_shipped_sync.isoformat()
        else:
            last_shipped_sync_str = ''

        # Convert the datetime object to a string value
        if self.last_readytopick_sync:
            last_readytopick_sync_str = self.last_readytopick_sync.isoformat()
        else:
            last_readytopick_sync_str = ''


        icp.set_param('delivery_goflow.last_inpicking_sync', last_inpicking_sync_str)
        icp.set_param('delivery_goflow.last_shipped_sync', last_shipped_sync_str)
        icp.set_param('delivery_goflow.last_readytopick_sync', last_readytopick_sync_str)

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

