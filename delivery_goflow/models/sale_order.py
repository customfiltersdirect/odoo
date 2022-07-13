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

class goflow_store(models.Model):
    _name = 'goflow.store'

    name = fields.Char('Name')
    goflow_id = fields.Char('Goflow ID')
    channel = fields.Char('Channel')
    sync_orders = fields.Boolean('Sync Orders',default=True)

    def sync_store_goflow(self):
        goflow_token = self.env['ir.config_parameter'].get_param('delivery_goflow.token_goflow')
        goflow_subdomain = self.env['ir.config_parameter'].get_param('delivery_goflow.subdomain_goflow')

        url = 'https://%s.api.goflow.com/v1/stores' % goflow_subdomain
        headers = {
            'X-Beta-Contact': self.env.user.partner_id.email
        }

        result = requests.get(url, auth=BearerAuth(goflow_token), headers=headers)
        goflow_api = result.json()
        stores = goflow_api["data"]

        while goflow_api["next"]:
            goflow_api = requests.get(goflow_api["next"], auth=BearerAuth(goflow_token), headers=headers).json()
            stores.extend(goflow_api["data"])
        for store in stores:
            goflow_store_id = store["id"]
            goflow_store_obj = self.env['goflow.store'].search([('goflow_id', '=', goflow_store_id)])
            if not goflow_store_obj:
                goflow_store_name = store["name"]
                goflow_store_channel = store["channel"]

                self.env['goflow.store'].create(
                    {'name': goflow_store_name, 'goflow_id': goflow_store_id, 'channel': goflow_store_channel})


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    goflow_id = fields.Char('Goflow ID')
    goflow_tracking_number = fields.Char('Goflow Tracking Ref')
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    goflow_id = fields.Char('Goflow ID')
    goflow_order_no = fields.Char('Goflow Order Number')
    goflow_order_status = fields.Char('Goflow Order Status')
    goflow_store_id = fields.Many2one('goflow.store','Store')
    goflow_invoice_no = fields.Char('Goflow Invoice No')
    goflow_po_no = fields.Char('Goflow PO No')
    goflow_carrier = fields.Char('Goflow Carrier')
    goflow_shipping_method = fields.Char('Goflow Shipping Method')
    goflow_scac = fields.Char('Goflow SCAC')
    goflow_shipped_at = fields.Datetime('Goflow Shipped At')
    goflow_store_latest_ship = fields.Date('Goflow Store Latest Ship')
    goflow_store_latest_delivery = fields.Date('Goflow Store Latest Delivery')

    def write(self, vals):
        goflow_order_status = vals.get('goflow_order_status')
        res = super(SaleOrder, self).write(vals)
        if goflow_order_status and 'ready_to_pick' in goflow_order_status:
            self.action_confirm()
        if goflow_order_status and 'shipped' in goflow_order_status:
            if self.state == 'draft':
                self.action_confirm()
            if self.picking_ids:
                for picking in self.picking_ids:
                    picking.action_assign()
                    picking.action_confirm()
                    for mv in picking.move_ids_without_package:
                        mv.quantity_done = mv.product_uom_qty
                    picking.button_validate()

            if not self.invoice_ids:
                self._create_invoices()

            if self.invoice_ids:
                for invoice in self.invoice_ids:
                    invoice.action_post()

        return res



    def convert_iso_to_utc(self,date):
        if date:
            if '.' in date:
                date = date.split(".")
                date = date[0] + 'Z'
            utc_date = str(dateutil.parser.isoparse(date))
            try:
                utc_date = utc_date.split("+")
                utc_date = utc_date[0]
            except:
                utc_date = datetime.now()
            return utc_date
        else:
            return False
    def sync_so_goflow(self):
        cron_job_id = self.env.ref('delivery_goflow.sync_order_from_goflow_ir_cron')
        lastcall = cron_job_id.lastcall
        print (lastcall)

        goflow_token = self.env['ir.config_parameter'].get_param('delivery_goflow.token_goflow')
        goflow_subdomain = self.env['ir.config_parameter'].get_param('delivery_goflow.subdomain_goflow')
        if lastcall:
            goflow_lastcall = lastcall.strftime('%Y-%m-%dT%H:%M:%SZ ')
            url = 'https://%s.api.goflow.com/v1/orders?filters[status_updated_at:gte]=%s' % (goflow_subdomain,str(goflow_lastcall))

        else:
            url = 'https://%s.api.goflow.com/v1/orders' % goflow_subdomain
        headers = {
            'X-Beta-Contact': self.env.user.partner_id.email
        }

        result = requests.get(url, auth=BearerAuth(goflow_token), headers=headers)
        goflow_api = result.json()
        orders = goflow_api["data"]
        print ("orders",orders)
        while goflow_api["next"]:
            goflow_api = requests.get(goflow_api["next"], auth=BearerAuth(goflow_token), headers=headers).json()
            orders.extend(goflow_api["data"])

        for order in orders:
            first_name = order["billing_address"]["first_name"]
            last_name = order["billing_address"]["last_name"]
            if first_name and last_name:
                print (order["billing_address"]["first_name"],order["billing_address"]["last_name"])
                partner_name = order["billing_address"]["first_name"] or '' + " " + order["billing_address"]["last_name"]
                partner_country_code = order["billing_address"]["country_code"]
                partner_street1 = order["billing_address"]["street1"]
                partner_street2 = order["billing_address"]["street2"]
                partner_city = order["billing_address"]["city"]
                partner_state = order["billing_address"]["state"]
                partner_zip = order["billing_address"]["zip_code"]
                # print ("1",partner_country_code)
                # country_id = self.env['res.country'].sudo().search([('name', '=', 'United States')], limit=1)
                # print ("country_id",country_id)
                # partner_state_obj = self.env['res.country.state'].search([
                #     ('name', '=', partner_state),
                #     ('country_id', '=', country_id)
                # ], limit=1)
                # print ("partner_state_obj",partner_state_obj)

                # partner_obj = self.env['res.partner'].search([('name','=',partner_name),('country_id','=',country_id)])
                partner_obj = self.env['res.partner'].search([('name','=',partner_name)])

                if not partner_obj:
                    # partner_obj = self.env['res.partner'].create({'name':partner_name,'country_id':country_id.id,'street1':partner_street1,'street2':partner_street2,'partner_zip':partner_zip,'city':partner_city,'state_id':partner_state_obj.id,'country_id':country_id})
                    partner_obj = self.env['res.partner'].create({'name':partner_name,})
                print ("2",partner_name)
                order_lines = order["lines"]
                goflow_date = order["date"]
                goflow_shipped_at = order["shipment"]["shipped_at"]
                goflow_store_latest_ship =order["ship_dates"]["store_provided_latest_ship"]
                goflow_store_latest_delivery =order["ship_dates"]["store_provided_latest_delivery"]

                goflow_id = order["id"]
                goflow_invoice_no = order["invoice_number"]
                goflow_po_no = order["purchase_order_number"]
                goflow_store_id = order["store"]["id"]
                goflow_shipment_carrier = order["shipment"]["carrier"]
                goflow_shipment_shipping_method = order["shipment"]["shipping_method"]
                goflow_shipment_scac = order["shipment"]["scac"]
                goflow_store_obj = self.env['goflow.store'].search([('goflow_id','=',goflow_store_id)])
                goflow_ship_boxes  = order["shipment"]["boxes"]
                tracking_line_list = []
                for box in goflow_ship_boxes:
                    tracking_line_dict = {}
                    tracking_number = box['tracking_number']
                    for line in box["lines"]:
                        tracking_line_dict['tracking_number'] = tracking_number
                        tracking_line_dict['order_line_id'] = line["order_line_id"]
                    if tracking_line_dict:
                        tracking_line_list.append(tracking_line_dict)



                if not goflow_store_obj:
                    goflow_store_name = order["store"]["name"]
                    goflow_store_id = order["store"]["id"]
                    goflow_store_channel = order["store"]["channel"]

                    goflow_store_obj = self.env['goflow.store'].create({'name':goflow_store_name,'goflow_id':goflow_store_id,'channel':goflow_store_channel})
                if goflow_store_obj.sync_orders:

                    check_if_order_exists = self.search([('goflow_id','=',goflow_id)])

                    goflow_order_no = order["order_number"]
                    goflow_order_status = order["status"]
                    print (goflow_order_status,goflow_id,goflow_order_no,goflow_date)
                    # order_date = datetime.datetime.fromisoformat(goflow_date)
                    order_date = self.convert_iso_to_utc(goflow_date)
                    goflow_shipped_at = self.convert_iso_to_utc(goflow_shipped_at)
                    goflow_store_latest_ship = self.convert_iso_to_utc(goflow_store_latest_ship)
                    goflow_store_latest_delivery = self.convert_iso_to_utc(goflow_store_latest_delivery)


                    if check_if_order_exists:
                        order = check_if_order_exists
                        order.goflow_invoice_no = goflow_invoice_no
                        order.goflow_po_no = goflow_po_no
                        order.goflow_carrier = goflow_shipment_carrier
                        order.goflow_shipping_method = goflow_shipment_shipping_method
                        order.goflow_scac = goflow_shipment_scac
                        order.goflow_order_status = goflow_order_status
                        order.goflow_shipped_at = goflow_shipped_at
                        order.goflow_store_latest_ship = goflow_store_latest_ship
                        order.goflow_store_latest_delivery = goflow_store_latest_delivery
                        for line in tracking_line_list:
                            goflow_line_id = line['order_line_id']
                            line_obj = self.env['sale.order.line'].search([('goflow_id','=',goflow_line_id)])
                            if line_obj:
                                line_obj.goflow_tracking_number = line['tracking_number']
                    if not check_if_order_exists:
                        order_vals = {}
                        order_vals['partner_id'] = partner_obj.id
                        order_vals['date_order'] = order_date
                        order_vals['goflow_id'] = goflow_id
                        order_vals['goflow_order_no'] = goflow_order_no
                        order_vals['goflow_order_status'] = goflow_order_status
                        order_vals['goflow_store_id'] = goflow_store_obj.id
                        order_vals["goflow_invoice_no"]=goflow_invoice_no
                        order_vals["goflow_po_no"] = goflow_po_no
                        order_vals["goflow_carrier"] = goflow_shipment_carrier
                        order_vals["goflow_shipping_method"] = goflow_shipment_shipping_method
                        order_vals["goflow_scac"] = goflow_shipment_scac
                        order_vals["goflow_shipped_at"] = goflow_shipped_at
                        order_vals["goflow_store_latest_ship"] = goflow_store_latest_ship
                        order_vals["goflow_store_latest_delivery"] = goflow_store_latest_delivery

                        print (order_vals)
                        so = self.env['sale.order'].create(order_vals)
                        print (so)
                        for line in order_lines:
                            goflow_product_id = line["product"]["id"]
                            product_obj = self.env["product.product"].search([('goflow_id','=',goflow_product_id)],limit=1)
                            product_qty = line["quantity"]["amount"]
                            product_price = line["charges"][0]["amount"]
                            goflow_line_id =line["id"]
                            tracking_obj = next(filter(lambda d: d.get('order_line_id') == goflow_line_id, tracking_line_list), None)
                            try:
                                tracking_number = tracking_obj['tracking_number']
                            except:
                                tracking_number = ''
                            sol = self.env['sale.order.line'].create({
                                'name': product_obj.name,
                                'product_id': product_obj.id,
                                'product_uom_qty': product_qty,
                                'product_uom': product_obj.uom_id.id,
                                'price_unit': product_price,
                                'order_id': so.id,
                                'tax_id':  False,
                                'goflow_id':goflow_line_id,
                                'goflow_tracking_number':tracking_number

                            })

            # if not check_if_order_exists:
            #     self.create({'goflow_id':goflow_id,'goflow_item_no':goflow_item_no})

