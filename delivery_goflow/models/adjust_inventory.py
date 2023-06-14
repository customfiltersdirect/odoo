from odoo import fields, models, api, tools, _
import requests
from .res_config_settings import BearerAuth
import base64
import json


class Adjust_inventory(models.Model):
    _inherit = 'product.product'

    def _split_batch(self, ids):
        batch_size = 1500
        for batch in tools.split_every(batch_size, ids):
            yield batch

    def adjust_inventory(self):
        goflow_token = self.env['ir.config_parameter'].get_param('delivery_goflow.token_goflow')
        goflow_subdomain = self.env['ir.config_parameter'].get_param('delivery_goflow.subdomain_goflow')

        url = 'https://%s.api.goflow.com/v1/inventory/adjustments' % goflow_subdomain
        headers = {
            'X-Beta-Contact': self.env.user.partner_id.email,
            'Content-Type': 'application/json'
        }

        filtered_products = self.sudo().search([
            ('goflow_id', '!=', False),
            ('standard_price', '>', 0)
        ]).ids
        for batch_ids in self._split_batch(filtered_products):
            product_ids = self.sudo().search([('id', 'in', list(batch_ids))])

            json_data = self._prepare_values(product_ids)

            json_string = json.dumps(json_data)
            result = requests.post(url, auth=BearerAuth(goflow_token), headers=headers, json=json_data)
            print(result)


    def _prepare_values(self, products):
         vals={}
         if products:
             vals.update({
                 "type": "absolute",
                 "warehouse_id": self.env['stock.warehouse'].search([('sync_orders', '=', True)],limit=1).goflow_id,
                 "reference_number": "",
                 "lines": [
                     {
                         "product_id": int(rec_id.goflow_id),
                         "quantity": int(rec_id.qty_available),
                         "cost": rec_id.standard_price,
                         "reason": "Odoo Inventory Export"
                     } for rec_id in products
                 ]

             })
         return vals






