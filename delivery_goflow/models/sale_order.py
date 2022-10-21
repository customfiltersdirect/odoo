# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import UserError
import requests
from odoo.http import request
from .res_config_settings import BearerAuth
from datetime import datetime,timezone,timedelta
from dateutil.tz import tzutc
import dateutil.parser


class AccountMove(models.Model):
    _inherit = 'account.move'

## Add goflow invoice id to odoo invoice
    goflow_invoice_no = fields.Char('Goflow Invoice No')




class goflow_store(models.Model):
    _name = 'goflow.store'

    name = fields.Char('Name')
    goflow_id = fields.Char('Goflow ID')
    channel = fields.Char('Channel')
    sync_orders = fields.Boolean('Sync Orders',default=False)
    partner_id = fields.Many2one('res.partner','Partner')

    @api.model
    def create(self, vals):
        store_name = vals.get('name')
        partner_obj = self.env['res.partner'].create({'name':store_name})
        vals['partner_id'] = partner_obj.id
        return super(goflow_store, self).create(vals)

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
    goflow_order_date = fields.Date('Goflow Order Date')
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

    def update_so_status(self,lastcall):
        if lastcall:
            find_updated_orders = self.search(['|',('write_date','>=',lastcall),('create_date','>=',lastcall)])
            for order in find_updated_orders:
                order.create_invoice_delivery()
        else:
            find_all_orders = self.search([])
            for order in find_all_orders:
                order.create_invoice_delivery()



    def create_invoice_delivery(self):
        if self.state == 'draft' and self.goflow_order_status =='in_picking' :
           self.action_confirm()
        if self.goflow_order_status in ('in_picking','in_packing'):
            if self.state == 'draft':
                self.action_confirm()
            if self.picking_ids:
                for picking in self.picking_ids.filtered(lambda x: x.state != 'cancel'):
                    if picking.state in ('waiting','confirmed'):
                        picking.action_assign()
                    # picking.action_confirm()
                    for mv in picking.move_ids_without_package:
                        if mv.product_uom_qty != 0.0:
                            mv.quantity_done = mv.product_uom_qty

        if self.goflow_order_status in ('shipped'):
            if self.state == 'draft':
                self.action_confirm()

            if self.picking_ids:
                for picking in self.picking_ids.filtered(lambda x: x.state != 'cancel'):
                    if picking.state in ('waiting','confirmed'):
                        picking.action_assign()
                    # picking.action_confirm()
                    for mv in picking.move_ids_without_package:
                        if mv.product_uom_qty != 0.0:
                            mv.quantity_done = mv.product_uom_qty

                    if picking.state != 'done':
                        picking.button_validate()


                if not self.invoice_ids:
                    self._create_invoices()

                if self.invoice_ids:
                    for invoice in self.invoice_ids.filtered(lambda x: x.state == 'draft'):
                        ## copy goflow invoice no to invoice in odoo
                        invoice.goflow_invoice_no = self.goflow_invoice_no
                        invoice.action_post()


    def api_call_for_sync_orders(self):
        cron_job_id = self.env.ref('delivery_goflow.sync_order_from_goflow_ir_cron')

        lastcall = cron_job_id.lastcall
        if lastcall:
            lastcall_delay = lastcall - timedelta(minutes=5)
        else:
            lastcall_delay = False
        self.sync_so_goflow(lastcall_delay)
        self.update_so_status(lastcall_delay)





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

    def get_store_param(self):
        total_stores = self.env['goflow.store'].search([])
        to_be_synced_stores = self.env['goflow.store'].search([('sync_orders','=',True)])
        if len(total_stores) == len(to_be_synced_stores):
            store_args = None
            return store_args
        else:
            store_args_list = []
            for store in to_be_synced_stores:
                store_args_list.append('filters[store.id]=%s'% (store.goflow_id,))
            if store_args_list:
                store_args = "&".join(store_args_list)
            else:
                store_args = None
            return store_args

    def get_warehouse_param(self,company_id):
        total_warehouse = self.env['stock.warehouse'].search([('company_id','=',company_id.id)])
        to_be_synced_warehouses = self.env['stock.warehouse'].search([('company_id','=',company_id.id),('sync_orders','=',True)])
        if len(total_warehouse) == len(to_be_synced_warehouses):
            warehouse_args = None
            return warehouse_args
        else:
            warehouse_args_list = []
            for ware in to_be_synced_warehouses:
                warehouse_args_list.append('filters[warehouse.id]=%s'% (ware.goflow_id,))
            if warehouse_args_list:
                warehouse_args = "&".join(warehouse_args_list)
            else:
                warehouse_args = None
            return warehouse_args





    def sync_so_goflow(self,lastcall):
        company_for_glow = self.env['res.company'].search([('use_for_goflow_api','=',True)],limit=1)
        goflow_token = self.env['ir.config_parameter'].get_param('delivery_goflow.token_goflow')
        goflow_subdomain = self.env['ir.config_parameter'].get_param('delivery_goflow.subdomain_goflow')
        goflow_cutoff_date = self.env['ir.config_parameter'].get_param('delivery_goflow.goflow_cutoff_date')

        store_args = self.get_store_param()
        warehouse_args = self.get_warehouse_param(company_for_glow)

        if lastcall:
            goflow_lastcall = lastcall.strftime('%Y-%m-%dT%H:%M:%SZ ')
            url = 'https://%s.api.goflow.com/v1/orders?filters[status_updated_at:gte]=%s' % (goflow_subdomain,str(goflow_lastcall))
            if store_args:
                url = url.rstrip()
                url += '&'+store_args
            if warehouse_args:
                url = url.rstrip()
                url += '&' + warehouse_args

        else:
            datetime_obj = datetime.strptime(goflow_cutoff_date, '%Y-%m-%d %H:%M:%S')

            goflow_cutoff = datetime_obj.strftime('%Y-%m-%dT%H:%M:%SZ ')
            # url = 'https://%s.api.goflow.com/v1/orders?filters[status]=ready_to_pick&filters[date:gte]=%s'  % (goflow_subdomain,str(goflow_cutoff))
            url = 'https://%s.api.goflow.com/v1/orders?filters[status]=ready_to_pick'  % (goflow_subdomain)
            if store_args:
                url = url.rstrip()
                url += '&'+store_args
            if warehouse_args:
                url = url.rstrip()
                url += '&' + warehouse_args
        headers = {
            'X-Beta-Contact': self.env.user.partner_id.email
        }
        result = requests.get(url, auth=BearerAuth(goflow_token), headers=headers, verify=False)
        goflow_api = result.json()
        orders = goflow_api["data"]
        while goflow_api["next"]:
            goflow_api = requests.get(goflow_api["next"], auth=BearerAuth(goflow_token), headers=headers).json()
            orders.extend(goflow_api["data"])
        for order in orders:
            goflow_store_id = order["store"]["id"]
            goflow_store_obj = self.env['goflow.store'].search([('goflow_id', '=', goflow_store_id)],limit=1)
            vals_partner_ship = {}
            vals_partner_ship['name'] = (order["shipping_address"]["first_name"] or '' )+ ((" " + (order["shipping_address"]["last_name"] or '')))
            partner_ship_country_code = order["shipping_address"]["country_code"]
            vals_partner_ship['street'] = order["shipping_address"]["street1"]
            vals_partner_ship['street2'] = order["shipping_address"]["street2"]
            vals_partner_ship['city'] = order["shipping_address"]["city"]
            partner_ship_state_code = order["shipping_address"]["state"]
            vals_partner_ship['zip'] = order["shipping_address"]["zip_code"]
            vals_partner_ship['email'] = order["billing_address"]["email"] or None
            vals_partner_ship['type'] = 'delivery'
            ship_country_id = self.env['res.country'].search([('code', '=', partner_ship_country_code.upper())], limit=1)
            if ship_country_id:
                vals_partner_ship['country_id'] = ship_country_id.id
                ship_state_id = self.env['res.country.state'].search([
                    ('code', '=', partner_ship_state_code),
                    ('country_id', '=', ship_country_id.id)
                ], limit=1)
                vals_partner_ship['state_id'] = ship_state_id and ship_state_id.id or False
            partner_ship_obj = self.env['res.partner'].search([('name','=',vals_partner_ship['name'])],limit=1)

            if not partner_ship_obj:
                vals_partner_ship['parent_id'] = goflow_store_obj.partner_id.id
                partner_ship_obj = self.env['res.partner'].create(vals_partner_ship)

            order_lines = order["lines"]
            goflow_date = order["date"]
            goflow_shipped_at = order["shipment"]["shipped_at"]
            goflow_store_latest_ship =order["ship_dates"]["store_provided_latest_ship"]
            goflow_store_latest_delivery =order["ship_dates"]["store_provided_latest_delivery"]

            goflow_id = order["id"]
            goflow_invoice_no = order["invoice_number"]
            goflow_po_no = order["purchase_order_number"]

            goflow_shipment_carrier = order["shipment"]["carrier"]
            goflow_shipment_shipping_method = order["shipment"]["shipping_method"]
            goflow_shipment_scac = order["shipment"]["scac"]
            goflow_ship_boxes  = order["shipment"]["boxes"]
            goflow_warehouse_id = order["warehouse"]["id"]
            goflow_warehouse_name = order["warehouse"]["name"]
            warehouse_obj = self.env['stock.warehouse'].search([('goflow_id','=',goflow_warehouse_id)],limit=1)
            if not warehouse_obj:
                warehouse_obj = self.env['stock.warehouse'].create({'name':goflow_warehouse_name,'goflow_id':goflow_warehouse_id,'code':goflow_warehouse_name[:2],'company_id':company_for_glow and company_for_glow.id or False,'sync_orders':True})
            tracking_line_list = []
            for box in goflow_ship_boxes:
                tracking_line_dict = {}
                tracking_number = box['tracking_number']
                for line in box["lines"]:
                    tracking_line_dict['tracking_number'] = tracking_number
                    tracking_line_dict['order_line_id'] = line["order_line_id"]
                if tracking_line_dict:
                    tracking_line_list.append(tracking_line_dict)
            check_if_order_exists = self.search([('goflow_id','=',goflow_id)],limit=1)
            goflow_order_no = order["order_number"]
            goflow_order_status = order["status"]
            order_date = self.convert_iso_to_utc(goflow_date)
            goflow_shipped_at = self.convert_iso_to_utc(goflow_shipped_at)
            goflow_store_latest_ship = self.convert_iso_to_utc(goflow_store_latest_ship)
            goflow_store_latest_delivery = self.convert_iso_to_utc(goflow_store_latest_delivery)

            if check_if_order_exists:
                order = check_if_order_exists
                vals_write = {}
                if order.warehouse_id != warehouse_obj:
                    order.action_cancel()
                    order.action_draft()
                    order.warehouse_id = warehouse_obj.id
                    order.action_confirm()
                vals_write['goflow_invoice_no'] = goflow_invoice_no
                vals_write['goflow_po_no'] = goflow_po_no
                vals_write['goflow_carrier'] = goflow_shipment_carrier
                vals_write['goflow_shipping_method'] = goflow_shipment_shipping_method
                vals_write['goflow_scac'] = goflow_shipment_scac
                vals_write['goflow_order_status'] = goflow_order_status
                vals_write['goflow_shipped_at'] = goflow_shipped_at
                vals_write['goflow_store_latest_ship'] = goflow_store_latest_ship
                vals_write['goflow_store_latest_delivery'] = goflow_store_latest_delivery
                vals_write['goflow_order_date'] = order_date
                order.write(vals_write)

                for line in tracking_line_list:
                    goflow_line_id = line['order_line_id']
                    line_obj = self.env['sale.order.line'].search([('goflow_id','=',goflow_line_id)],limit=1)
                    if line_obj:
                        line_obj.goflow_tracking_number = line['tracking_number']
            if not check_if_order_exists:
                order_vals = {}
                order_vals['partner_id'] = goflow_store_obj.partner_id.id
                order_vals['partner_shipping_id'] = partner_ship_obj and partner_ship_obj.id or goflow_store_obj.partner_id.id

                order_vals['date_order'] = order_date
                order_vals['warehouse_id'] = warehouse_obj.id
                order_vals['goflow_id'] = goflow_id
                order_vals['goflow_order_no'] = goflow_order_no
                order_vals['goflow_order_date'] = order_date
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
                order_vals["company_id"]= company_for_glow and company_for_glow.id or False
                so = self.env['sale.order'].create(order_vals)
                for line in order_lines:
                    goflow_product_id = line["product"]["id"]
                    goflow_product_name = line["product"]["description"]
                    goflow_product_item_no = line["product"]["item_number"]
                    product_obj = self.env["product.product"].search([('goflow_id','=',goflow_product_id)],limit=1)
                    if not product_obj:
                        product_obj =  self.env['product.product'].create({'name':goflow_product_name,'goflow_id':goflow_product_id,'goflow_item_no':goflow_product_item_no,'company_id': company_for_glow and company_for_glow.id or False})


                    product_qty = line["quantity"]["amount"]
                    try:
                        product_price = line["charges"][0]["amount"]
                    except:
                        product_price = 0
                    goflow_line_id =line["id"]
                    tracking_obj = next(filter(lambda d: d.get('order_line_id') == goflow_line_id, tracking_line_list), None)
                    try:
                        tracking_number = tracking_obj['tracking_number']
                    except:
                        tracking_number = ''
                    self.env['sale.order.line'].create({
                        'name': product_obj and product_obj.name or 'Test',
                        'product_id': product_obj and product_obj.id or False,
                        'product_uom_qty': product_qty,
                        'product_uom': product_obj and product_obj.uom_id.id or False,
                        'price_unit': product_price,
                        'order_id': so.id,
                        'tax_id':  False,
                        'goflow_id':goflow_line_id,
                        'goflow_tracking_number':tracking_number

                    })
