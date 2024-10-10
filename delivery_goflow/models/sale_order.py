# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools
import requests
from .res_config_settings import BearerAuth
from datetime import datetime
import dateutil.parser
import logging
import datetime
from datetime import datetime, timedelta
from pytz import timezone, utc

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    ## Add goflow invoice id to odoo invoice
    goflow_invoice_no = fields.Char('Goflow Invoice No')
    goflow_order_no_ = fields.Char(string="Goflow Order Number", compute="compute_goflow_order_no", search='_search_glflow_order_no')

    def _search_glflow_order_no(self, operator, value):
        domain = [('goflow_order_no', operator, value)]
        order_ids = self.env['sale.order'].search(domain)
        goflow_orders = order_ids.filtered(lambda l: l.goflow_invoice_no).mapped('goflow_invoice_no')
        return [('goflow_invoice_no', operator, goflow_orders)]

    @api.depends('goflow_invoice_no')
    def compute_goflow_order_no(self):
        for rec in self:
            order_id = self.env['sale.order'].search([('goflow_invoice_no', '=', rec.goflow_invoice_no)])
            if order_id:
                rec.goflow_order_no_ = " , ".join(order_id.filtered(lambda l: l.goflow_order_no).mapped('goflow_order_no'))
            else:
                rec.goflow_order_no_ = False

class goflow_store(models.Model):
    _name = 'goflow.store'

    name = fields.Char('Name')
    goflow_id = fields.Char('Goflow ID')
    channel = fields.Char('Channel')
    sync_orders = fields.Boolean('Sync Orders', default=False)
    partner_id = fields.Many2one('res.partner', 'Partner')

    @api.model
    def create(self, vals):
        store_name = vals.get('name')
        partner_obj = self.env['res.partner'].create({'name': store_name})
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


def get_order_list_param(order_list):
    order_args_list = []
    order_args = None
    for order in order_list:
        order_args_list.append('filters[order_number]=%s' % (order))
    if order_args_list:
        order_args = "&".join(order_args_list)
    return order_args


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    goflow_id = fields.Char('Goflow ID')
    goflow_order_no = fields.Char('Goflow Order Number')
    goflow_order_date = fields.Date('Goflow Order Date')
    goflow_order_datetime = fields.Char('Goflow Order DateTime')

    goflow_order_status = fields.Char('Goflow Order Status')
    goflow_pick_list_number = fields.Char('Goflow Pick List Number')
    goflow_store_id = fields.Many2one('goflow.store', 'Store')
    goflow_invoice_no = fields.Char('Goflow Invoice No')
    goflow_po_no = fields.Char('Goflow PO No')
    goflow_carrier = fields.Char('Goflow Carrier')
    goflow_shipping_method = fields.Char('Goflow Shipping Method')
    goflow_scac = fields.Char('Goflow SCAC')
    goflow_shipped_at = fields.Datetime('Goflow Shipped At')
    goflow_store_latest_ship = fields.Datetime('Goflow Store Latest Ship')
    goflow_store_latest_delivery = fields.Date('Goflow Store Latest Delivery')
    goflow_shipped_last_call_check = fields.Boolean('Goflow Last Call check', index=True)
    goflow_full_invoiced = fields.Boolean('Goflow Total invoiced', index=True)
    active = fields.Boolean('Active', default=True, index=True)

    def _create_batch_transfers(self, in_picking_orders):
        in_picking_orders = in_picking_orders.filtered(lambda rin_o: rin_o.goflow_pick_list_number).sorted(key=lambda rin_o: rin_o.goflow_pick_list_number)
        pick_list_number = in_picking_orders[0].goflow_pick_list_number
        picking_ids = []
        for order in in_picking_orders:
            if order.goflow_pick_list_number != pick_list_number:
                if not picking_ids:
                    # pickings = order.picking_ids.filtered(lambda e: e.picking_type_id.code in ['incoming', 'internal'])
                    pickings = order.picking_ids.filtered(lambda e: e.picking_type_id.is_creating_batch)
                    for picking in pickings:
                        picking_ids.append(picking.id)
                if picking_ids:
                    old_batch = self.env['stock.picking.batch'].search([('goflow_pick_list_number', '=', pick_list_number)])
                    if old_batch:
                        link_pickings = []
                        for picking in picking_ids:
                            link_pickings.append((4, picking))
                        if link_pickings:
                            old_batch.write({'picking_ids': link_pickings})
                    else:
                        batch = self.env['stock.picking.batch'].create({
                            'user_id': order.user_id.id or self.env.user.id,
                            'company_id': order.company_id.id or self.env.company.id,
                            'picking_type_id': self.env['stock.picking'].browse(picking_ids[0]).picking_type_id.id,
                            'picking_ids': picking_ids,
                            'goflow_pick_list_number': pick_list_number
                        })
                        p_names = []
                        for p in batch.picking_ids:
                            p_names.append(p.name)
                        _logger.warning("Batch Created with these pickings %s ", ' '.join(p_names))
                        batch.action_confirm()
                pick_list_number = order.goflow_pick_list_number
                picking_ids = []
                # pickings = order.picking_ids.filtered(lambda e: e.picking_type_id.code in ['incoming', 'internal'])
                pickings = order.picking_ids.filtered(lambda e: e.picking_type_id.is_creating_batch)
                for picking in pickings:
                    picking_ids.append(picking.id)
            else:
                # pickings = order.picking_ids.filtered(lambda e: e.picking_type_id.code in ['incoming', 'internal'])
                pickings = order.picking_ids.filtered(lambda e: e.picking_type_id.is_creating_batch)
                for picking in pickings:
                    picking_ids.append(picking.id)
        if picking_ids:
            old_batch = self.env['stock.picking.batch'].search([('goflow_pick_list_number', '=', pick_list_number)])
            if old_batch:
                link_pickings = []
                for picking in picking_ids:
                    link_pickings.append((4, picking))
                if link_pickings:
                    old_batch.write({'picking_ids': link_pickings})
            else:
                batch = self.env['stock.picking.batch'].create({
                    'user_id': in_picking_orders[0].user_id.id or self.env.user.id,
                    'company_id': in_picking_orders[0].company_id.id or self.env.company.id,
                    'picking_type_id': self.env['stock.picking'].browse(picking_ids[0]).picking_type_id.id,
                    'picking_ids': picking_ids,
                    'goflow_pick_list_number': pick_list_number
                })
                p_names = []
                for p in batch.picking_ids:
                    p_names.append(p.name)
                _logger.warning("Batch Created with these pickings %s ", ' '.join(p_names))
                batch.action_confirm()

    def update_so_status(self, lastcall):
        if lastcall:
            find_updated_orders = self.search(['|', ('write_date', '>=', lastcall), ('create_date', '>=', lastcall)])
            i = 1
            for order in find_updated_orders:
                i += 1
                # print(i)
                # print(order.name)
                order.create_invoice_delivery()
            in_picking_orders = find_updated_orders.filtered(lambda o: o.goflow_order_status == 'in_picking')
            if in_picking_orders:
                self._create_batch_transfers(in_picking_orders)
        else:
            find_all_orders = self.search([])
            for order in find_all_orders:
                order.create_invoice_delivery()

    def update_so_invoice_delivery(self):
        sync_indexes = self.env['goflow.sync.index'].search([('synced_orders', '=', False)])
        counter = 1
        for sync_index in sync_indexes:
            _logger.info("------------Running Invoice Delivery by Index ID--------------------")
            _logger.info("Index Progress %s/%s" % (counter, len(sync_indexes.ids)))
            counter += 1

            order_ids = sync_index.order_ids
            for order in order_ids:
                # _logger.info(count)
                _logger.info("------------GO FLOW ORDER ID--------------------")
                _logger.info(order)
                order.create_invoice_delivery()

            self.env.cr.commit()
            sync_index.synced_orders = True

    def update_so_batch_transfers(self):
        sync_indexes = self.env['goflow.sync.index'].search([('synced_transfers', '=', False)])
        for sync_index in sync_indexes:
            order_ids = sync_index.order_ids
            if order_ids:
                in_picking_orders = order_ids.filtered(lambda o: o.goflow_order_status == 'in_picking')
                if in_picking_orders:
                    self._create_batch_transfers(in_picking_orders)
            sync_index.synced_transfers = True

    def create_invoice_delivery(self):
        goflow_order_status = self.goflow_order_status or ''
        order_state = self.state

        if goflow_order_status == 'in_picking':
            if order_state == 'draft':
                self.action_confirm()
            if self.picking_ids:
                for picking in self.picking_ids.filtered(lambda x: x.state != 'cancel'):
                    if picking.state in ('waiting', 'confirmed'):
                        picking.action_assign()

        if goflow_order_status == 'shipped':
            if order_state == 'draft':
                self.action_confirm()

            if self.picking_ids:
                for picking in self.picking_ids.filtered(lambda x: x.state != 'cancel'):
                    note = picking.note or ""
                    
                    # Processing Delivery orders (transfers) with status: assigned/Ready
                    if picking.picking_type_id.code == 'outgoing' and picking.state == 'assigned':
                        try:
                            picking.button_validate()
                            note += f"Was fully reserved: Validation successful. "
                            
                        except Exception as e:
                            note += f"Was fully reserved: Validation UNsuccessful. Error: {str(e)}. Cycling Reservation now. "
                            
                            picking.do_unreserve()
                            note += f"Unreserved. "
                            
                            picking.action_assign()
                            note += f"Reserved back. "
                            
                            try:
                                picking.button_validate()
                                note += f"After Cycling Reservation: Validation successful. "
                                
                            except Exception as e:
                                note += f"After Cycling Reservation: Validation UNsuccessful. Error: {str(e)}. "
                        
                        picking.write({'note': note})
                            
                    # Processing Delivery orders (transfers) with status: confirmed/Waiting and waiting/Waiting Another Operation
                    if picking.picking_type_id.code == 'outgoing' and picking.state in ('confirmed', 'waiting'):
                        try:
                            # forcing quantities for whatever is short
                            for move in picking.move_ids:
                                if move.quantity != move.product_uom_qty:
                                    move.write({'quantity': move.product_uom_qty})
                            
                            picking.button_validate()
                            note += f"After quantities were forced: Validation successful"
                            
                        except Exception as e:
                            note += f"Validation after forcing quantities failed with error:  {str(e)}. Unreserving. "
                            picking.do_unreserve()
                            
                            picking.action_assign()
                            note += f"Reserved back. Forcing quantities. Status was {picking.state}"
                            
                            # since reservation was cycled - forcing quantities again for whatever is short
                            for move in picking.move_ids:
                                if move.quantity != move.product_uom_qty:
                                    move.write({'quantity': move.product_uom_qty})
                            
                            try:
                                picking.button_validate()
                                note += f"After Cycling Reservation and forcing quantities: Validation successful"
                            
                            except Exception as e:
                                note += f"After Cycling Reservation and forcing quantities: Validation failed with error:  {str(e)}. "
                        
                        picking.write({'note': note})

            if not self.invoice_ids:
                self._create_invoices()
            if self.invoice_ids:
                unmarked_invoices = self.invoice_ids.filtered(lambda x: not x.goflow_invoice_no)
                if unmarked_invoices and self.goflow_invoice_no:
                    for unmarked_invoice in unmarked_invoices:
                        unmarked_invoice.goflow_invoice_no = self.goflow_invoice_no

                for invoice in self.invoice_ids.filtered(lambda x: x.state == 'draft'):
                    ## copy goflow invoice no to invoice in odoo
                    invoice.goflow_invoice_no = self.goflow_invoice_no
                    invoice.action_post()

                self.goflow_full_invoiced = True
                # print("Invoiced")

    def _prepare_batch_values(self):
        return {}

    def api_call_for_sync_orders_in_picking(self, call_for_index=False, date_range=False):
        cron_job_id = self.env.ref('delivery_goflow.sync_order_in_picking_from_goflow_ir_cron')
        goflow_state = 'in_picking'

        calling_date_time = fields.Datetime.now()

        lastcall_delay = self.env['ir.config_parameter'].sudo().get_param('delivery_goflow.last_inpicking_sync')
        if lastcall_delay:
            lastcall_delay = datetime.fromisoformat(lastcall_delay)
        else:
            lastcall_delay = cron_job_id.lastcall

        lastcall_delay_new = lastcall_delay - timedelta(days=1)
        self.sync_so_goflow(lastcall_delay_new, goflow_state, date_range, update_sync_index=True)
        if not date_range:
            self.env['ir.config_parameter'].sudo().set_param('delivery_goflow.last_inpicking_sync', calling_date_time)

        # self.update_so_status(lastcall_delay_new)


    def api_call_orders_sweep2(self):
        # print("W")
        order_ids = self.search([]).filtered(lambda l: l.invoice_ids)
        count = 1
        for order in order_ids:
            print("%s/%s" % (count, len(order_ids)))
            count += 1
            unmarked_invoices = order.invoice_ids.filtered(lambda x: not x.goflow_invoice_no)
            if unmarked_invoices and order.goflow_invoice_no:
                for unmarked_invoice in unmarked_invoices:
                    unmarked_invoice.goflow_invoice_no = order.goflow_invoice_no
                    self.env.cr.commit()

    def api_call_orders_sweep1(self, orders=False):
        lastcall_delay = self.env['ir.config_parameter'].sudo().get_param('delivery_goflow.goflow_cutoff_date')
        if lastcall_delay:
            date_from = datetime.fromisoformat(lastcall_delay)

            daterange = {
                'date_from': date_from,
                'date_to': date_from
            }
            self.sync_update_so_goflow(lastcall=date_from, goflow_state="shipped", date_range=daterange, orders=orders)
            self.env.cr.commit()

            import time
            time.sleep(60)
            lastcall = self.env['ir.config_parameter'].sudo().get_param('delivery_goflow.goflow_cutoff_date')
            if lastcall:
                date_from = datetime.fromisoformat(lastcall)
                date_from = date_from + timedelta(days=1)
                self.env['ir.config_parameter'].sudo().set_param('delivery_goflow.goflow_cutoff_date', date_from)
                self.api_call_orders_sweep1()


    def api_call_for_sync_orders_shipped(self, call_for_index=False, date_range=False):
        cron_job_id = self.env.ref('delivery_goflow.sync_order_shipped_from_goflow_ir_cron')
        goflow_state = 'shipped'

        calling_date_time = fields.Datetime.now()

        lastcall_delay = self.env['ir.config_parameter'].sudo().get_param('delivery_goflow.last_shipped_sync')
        if lastcall_delay:
            lastcall_delay = datetime.fromisoformat(lastcall_delay)
        else:
            lastcall_delay = cron_job_id.lastcall


        lastcall_delay_new = lastcall_delay - timedelta(days=1)
        self.sync_so_goflow(lastcall_delay_new, goflow_state, date_range, update_sync_index=True)
        if not date_range:
            self.env['ir.config_parameter'].sudo().set_param('delivery_goflow.last_shipped_sync', calling_date_time)

        # self.update_shipped_so_status()
        # self.update_so_status(lastcall_delay)

    def api_call_for_sync_orders_shipped_invoice(self):
        self.update_so_invoice_delivery()
        # find_updated_orders = self.search([('goflow_shipped_last_call_check', '=', True), ('goflow_full_invoiced', '=', False)], limit=400)
        # for order in find_updated_orders:
        #     order.create_invoice_delivery()

    def update_shipped_so_status(self):
        sync_indexes = self.env['goflow.sync.index'].search([('synced_shipped', '=', False)])
        for sync_index in sync_indexes:
            order_ids = sync_index.order_ids
            if order_ids:
                find_updated_orders = order_ids.filtered(
                    lambda o: o.goflow_shipped_last_call_check and not o.goflow_full_invoiced and o.state == 'draft')
                for order in find_updated_orders:
                    order.action_confirm()
                    order.env.cr.commit()
            sync_index.synced_shipped = True

    def update_shipped_so_order_status(self, order_id):
        if not order_id.goflow_full_invoiced and order_id.state == 'draft':
            order_id.action_confirm()
            # order_id.env.cr.commit()


    def api_call_for_sync_orders_in_packing(self):
        cron_job_id = self.env.ref('delivery_goflow.sync_order_in_packing_from_goflow_ir_cron')

        lastcall = cron_job_id.lastcall
        if lastcall:
            lastcall_delay = lastcall
        else:
            lastcall_delay = False
        goflow_state = 'in_packing'
        # self.sync_so_goflow(lastcall_delay,goflow_state)
        # self.update_so_status(lastcall_delay)

    def api_call_for_sync_orders_ready_to_pick(self, call_for_index=False, date_range=False):
        cron_job_id = self.env.ref('delivery_goflow.sync_order_ready_to_pick_from_goflow_ir_cron')
        goflow_state = 'ready_to_pick'

        calling_date_time = fields.Datetime.now()

        lastcall_delay = self.env['ir.config_parameter'].sudo().get_param('delivery_goflow.last_readytopick_sync')
        if lastcall_delay:
            lastcall_delay = datetime.fromisoformat(lastcall_delay)
        else:
            lastcall_delay = cron_job_id.lastcall

        lastcall_delay_new = lastcall_delay - timedelta(days=1)
        self.sync_so_goflow(lastcall_delay_new, goflow_state, date_range, update_sync_index=True)
        if not date_range:
            self.env['ir.config_parameter'].sudo().set_param('delivery_goflow.last_readytopick_sync', calling_date_time)

        # self.update_so_status(lastcall_delay)

    def convert_iso_to_utc(self, date):
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
        to_be_synced_stores = self.env['goflow.store'].search([('sync_orders', '=', True)])
        if len(total_stores) == len(to_be_synced_stores):
            store_args = None
            return store_args
        else:
            store_args_list = []
            for store in to_be_synced_stores:
                store_args_list.append('filters[store.id]=%s' % (store.goflow_id,))
            if store_args_list:
                store_args = "&".join(store_args_list)
            else:
                store_args = None
            return store_args

    def _prepare_order_parameter(self, company_id, orders=False):
        if orders:
            total_orders = self.env['sale.order'].browse(orders)
        else:
            total_orders = self.env['sale.order'].search([
                ('company_id', '=', company_id.id),
                ('goflow_id', '!=', False),
                ('goflow_invoice_no', '=', False)], limit=200, order='goflow_order_date'
            )

        warehouse_args = False

        warehouse_args_list = []
        for order in total_orders:
            warehouse_args_list.append('filters[order_number]=%s' % (order.goflow_order_no,))
        if warehouse_args_list:
            warehouse_args = "&".join(warehouse_args_list)
        else:
            warehouse_args = None
        return warehouse_args

    def get_warehouse_param(self, company_id):
        total_warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id.id)])
        to_be_synced_warehouses = self.env['stock.warehouse'].search(
            [('company_id', '=', company_id.id), ('sync_orders', '=', True)])
        if len(total_warehouse) == len(to_be_synced_warehouses):
            warehouse_args = None
            return warehouse_args
        else:
            warehouse_args_list = []
            for ware in to_be_synced_warehouses:
                warehouse_args_list.append('filters[warehouse.id]=%s' % (ware.goflow_id,))
            if warehouse_args_list:
                warehouse_args = "&".join(warehouse_args_list)
            else:
                warehouse_args = None
            return warehouse_args

    def _prepare_partner_values(self, order):
        partner_ship_country_code = order["shipping_address"]["country_code"]
        partner_ship_state_code = order["shipping_address"]["state"]
        ship_country_obj = self.env['res.country'].search([('code', '=', partner_ship_country_code.upper())],
                                                          limit=1)
        vals_partner_ship = {
            'name': (order["shipping_address"]["first_name"] or '') +
                    (" " + (order["shipping_address"]["last_name"] or '')),
            'street': order["shipping_address"]["street1"],
            'street2': order["shipping_address"]["street2"],
            'city': order["shipping_address"]["city"],
            'zip': order["shipping_address"]["zip_code"],
            'email': order["billing_address"]["email"] or None,
            'type': 'delivery'
        }
        if ship_country_obj:
            ship_country_id = ship_country_obj.id
            vals_partner_ship['country_id'] = ship_country_id
            ship_state_id = self.env['res.country.state'].search([
                ('code', '=', partner_ship_state_code),
                ('country_id', '=', ship_country_id)
            ], limit=1)
            vals_partner_ship['state_id'] = ship_state_id and ship_state_id.id or False
        return vals_partner_ship

    def _prepare_edit_order_values(self, order):
        tracking_line_list = []
        for box in order["shipment"]["boxes"]:
            tracking_line_dict = {}
            tracking_number = box['tracking_number']
            for line in box["lines"]:
                tracking_line_dict['tracking_number'] = tracking_number
                tracking_line_dict['order_line_id'] = line["order_line_id"]
            if tracking_line_dict:
                tracking_line_list.append(tracking_line_dict)
        order_date = self.convert_iso_to_utc(order["date"])
        goflow_shipped_at = self.convert_iso_to_utc(order["shipment"]["shipped_at"])
        goflow_store_latest_ship = self.convert_iso_to_utc(order["ship_dates"]["store_provided_latest_ship"])
        goflow_store_latest_delivery = self.convert_iso_to_utc(order["ship_dates"]["store_provided_latest_delivery"])

        values_order = {
            'goflow_invoice_no': order["invoice_number"],
            'goflow_po_no': order["purchase_order_number"],
            'goflow_carrier': order["shipment"]["carrier"],
            'goflow_shipping_method': order["shipment"]["shipping_method"],
            'goflow_scac': order["shipment"]["scac"],
            'goflow_order_status': order["status"],
            'goflow_shipped_last_call_check': True if order["status"] == 'shipped' else False,
            'goflow_shipped_at': goflow_shipped_at,
            'goflow_store_latest_ship': goflow_store_latest_ship,
            'goflow_store_latest_delivery': goflow_store_latest_delivery,
            'goflow_order_date': order_date,
            'goflow_order_datetime': order_date,
            'goflow_pick_list_number': order["pick_list_number"],
        }
        return values_order

    def _prepare_order_values(self, order, company_for_glow, warehouse_obj_id):
        order_date = self.convert_iso_to_utc(order["date"])
        goflow_shipped_at = self.convert_iso_to_utc(order["shipment"]["shipped_at"])
        goflow_store_latest_ship = self.convert_iso_to_utc(order["ship_dates"]["store_provided_latest_ship"])
        goflow_store_latest_delivery = self.convert_iso_to_utc(order["ship_dates"]["store_provided_latest_delivery"])

        return {
            'date_order': order_date,
            'partner_id': self.env.ref('delivery_goflow.print_node_demo_partner').id,
            'goflow_order_no': order["order_number"],
            'goflow_order_date': order_date,
            'goflow_order_datetime': order_date,
            'goflow_order_status': order["status"],
            'goflow_shipped_last_call_check': True if order["status"] == 'shipped' else False,
            'goflow_invoice_no': order["invoice_number"],
            'goflow_po_no': order["purchase_order_number"],
            'goflow_carrier': order["shipment"]["carrier"],
            'goflow_shipping_method': order["shipment"]["shipping_method"],
            'goflow_scac': order["shipment"]["scac"],
            'goflow_shipped_at': goflow_shipped_at,
            'goflow_store_latest_ship': goflow_store_latest_ship,
            'goflow_store_latest_delivery': goflow_store_latest_delivery,
            'goflow_pick_list_number': order["pick_list_number"],
            'company_id': company_for_glow and company_for_glow.id or False,
            'warehouse_id': warehouse_obj_id,
        }

    def _prepare_order_lines(self, line, so, tracking_line_list, company_for_glow):
        goflow_product_id = line["product"]["id"]
        goflow_item_no = line["product"]["item_number"]
        product_obj = self.env["product.product"].search(['|' , ('goflow_id_var', '=', goflow_product_id),
                                                          ('goflow_item_no_var', '=', goflow_item_no)], limit=1)

        if not product_obj:
            product_vals = {'name': line["product"]["description"], 'goflow_id_var': goflow_product_id,
                            'goflow_item_no_var': line["product"]["item_number"], 'detailed_type': 'product',
                            'company_id': company_for_glow and company_for_glow.id or False}
            product_obj = self.env['product.product'].create(product_vals)
        try:
            product_price = line["charges"][0]["amount"]
        except:
            product_price = 0
        tracking_obj = next(filter(lambda d: d.get('order_line_id') == line["id"], tracking_line_list),
                            None)
        try:
            tracking_number = tracking_obj['tracking_number']
        except:
            tracking_number = ''
        return {
            'name': product_obj and product_obj.name or 'Test',
            'product_id': product_obj and product_obj.id or False,
            'product_uom_qty': line["quantity"]["amount"],
            'product_uom': product_obj and product_obj.uom_id.id or False,
            'price_unit': product_price,
            'order_id': so.id,
            'tax_id': False,
            'goflow_id': line["id"],
            'goflow_tracking_number': tracking_number
        }

    def _preparing_url_by_orders(self, company_for_glow, orders):
        goflow_subdomain = self.env['ir.config_parameter'].get_param('delivery_goflow.subdomain_goflow')
        store_args = self.get_store_param()
        warehouse_args = self.get_warehouse_param(company_for_glow)
        url = 'https://%s.api.goflow.com/v1/orders?' % goflow_subdomain
        # print('url',url)
        if store_args:
            url = url.rstrip()
            url += '&' + store_args
        if warehouse_args:
            url = url.rstrip()
            url += '&' + warehouse_args
        if orders:
            url = url.rstrip()
            url += '&' + orders
        return url

    def _preparing_url2(self, lastcall, date_range, company_for_glow, goflow_state):
        goflow_subdomain = self.env['ir.config_parameter'].get_param('delivery_goflow.subdomain_goflow')
        store_args = self.get_store_param()
        warehouse_args = self.get_warehouse_param(company_for_glow)
        if date_range:
            date_from = date_range.get('date_from')
            date_to = date_range.get('date_to')
            print(date_range)
            date_from_str = date_from.strftime('%Y-%m-%dT%H:%M:%SZ')
            date_to_str = date_to.strftime('%Y-%m-%dT23:59:59Z')
            if goflow_state == 'shipped':
                url = 'https://%s.api.goflow.com/v1/orders?filters[date:gte]=%s&filters[date:lte]=%s' % (
            goflow_subdomain, str(date_from_str), str(date_to_str))
            else:
                url = 'https://%s.api.goflow.com/v1/orders?filters[date:gte]=%s&filters[date:lte]=%s' % (
                    goflow_subdomain, str(date_from_str), str(date_to_str))
            # print('url',url)
            if store_args:
                url = url.rstrip()
                url += '&' + store_args
            if warehouse_args:
                url = url.rstrip()
                url += '&' + warehouse_args
            return url
        elif lastcall:
            # print(lastcall)
            ll = lastcall.replace(hour=0, minute=0, second=0, microsecond=0)
            goflow_lastcall = ll.strftime('%Y-%m-%dT%H:%M:%SZ ')
            # Convert the start of the day datetime object to a string
            print(goflow_lastcall)
            # goflow_lastcall = yesterday_str
            if goflow_state == 'shipped':
                url = 'https://%s.api.goflow.com/v1/orders?filters[status]=%s&filters[status_updated_at:gte]=%s' % (
            goflow_subdomain, goflow_state, str(goflow_lastcall))
            else:
                url = 'https://%s.api.goflow.com/v1/orders?filters[status]=%s&filters[date:gte]=%s' % (
                    goflow_subdomain, goflow_state, str(goflow_lastcall))
            # print('url',url)
            if store_args:
                url = url.rstrip()
                url += '&' + store_args
            if warehouse_args:
                url = url.rstrip()
                url += '&' + warehouse_args
            return url
        else:
            # datetime_obj = datetime.strptime(goflow_cutoff_date, '%Y-%m-%d %H:%M:%S')
            # goflow_cutoff = datetime_obj.strftime('%Y-%m-%dT%H:%M:%SZ ')
            # url = 'https://%s.api.goflow.com/v1/orders?filters[status]=ready_to_pick&filters[date:gte]=%s'  % (goflow_subdomain,str(goflow_cutoff))
            url = 'https://%s.api.goflow.com/v1/orders?filters[status]=%s' % (goflow_subdomain, goflow_state)
            if store_args:
                url = url.rstrip()
                url += '&' + store_args
            if warehouse_args:
                url = url.rstrip()
                url += '&' + warehouse_args
            return url

    def _preparing_url(self, lastcall, date_range, company_for_glow, goflow_state):
        goflow_subdomain = self.env['ir.config_parameter'].get_param('delivery_goflow.subdomain_goflow')
        store_args = self.get_store_param()
        warehouse_args = self.get_warehouse_param(company_for_glow)
        if date_range:
            date_from = date_range.get('date_from')
            date_to = date_range.get('date_to')
            print(date_range)
            date_from_str = date_from.strftime('%Y-%m-%dT%H:%M:%SZ')
            date_to_str = date_to.strftime('%Y-%m-%dT23:59:59Z')
            if goflow_state=='shipped' :
                url = 'https://%s.api.goflow.com/v1/orders?filters[status]=%s&filters[status_updated_at:gte]=%s&filters[status_updated_at:lte]=%s' % (
            goflow_subdomain, goflow_state, str(date_from_str), str(date_to_str))
            else:
                url = 'https://%s.api.goflow.com/v1/orders?filters[status]=%s&filters[date:gte]=%s&filters[date:lte]=%s' % (
                    goflow_subdomain, goflow_state, str(date_from_str), str(date_to_str))
            # print('url',url)
            if store_args:
                url = url.rstrip()
                url += '&' + store_args
            if warehouse_args:
                url = url.rstrip()
                url += '&' + warehouse_args
            return url
        elif lastcall:
            # print(lastcall)
            ll = lastcall.replace(hour=0, minute=0, second=0, microsecond=0)
            goflow_lastcall = ll.strftime('%Y-%m-%dT%H:%M:%SZ ')
            # Convert the start of the day datetime object to a string
            print(goflow_lastcall)
            # goflow_lastcall = yesterday_str
            if goflow_state == 'shipped':
                url = 'https://%s.api.goflow.com/v1/orders?filters[status]=%s&filters[status_updated_at:gte]=%s' % (
            goflow_subdomain, goflow_state, str(goflow_lastcall))
            else:
                url = 'https://%s.api.goflow.com/v1/orders?filters[status]=%s&filters[date:gte]=%s' % (
                    goflow_subdomain, goflow_state, str(goflow_lastcall))
            # print('url',url)
            if store_args:
                url = url.rstrip()
                url += '&' + store_args
            if warehouse_args:
                url = url.rstrip()
                url += '&' + warehouse_args
            return url
        else:
            # datetime_obj = datetime.strptime(goflow_cutoff_date, '%Y-%m-%d %H:%M:%S')
            # goflow_cutoff = datetime_obj.strftime('%Y-%m-%dT%H:%M:%SZ ')
            # url = 'https://%s.api.goflow.com/v1/orders?filters[status]=ready_to_pick&filters[date:gte]=%s'  % (goflow_subdomain,str(goflow_cutoff))
            url = 'https://%s.api.goflow.com/v1/orders?filters[status]=%s' % (goflow_subdomain, goflow_state)
            if store_args:
                url = url.rstrip()
                url += '&' + store_args
            if warehouse_args:
                url = url.rstrip()
                url += '&' + warehouse_args
            return url

    def _preparing_url_specific_orders(self, company_for_glow, goflow_state, order_list):
        goflow_subdomain = self.env['ir.config_parameter'].get_param('delivery_goflow.subdomain_goflow')
        store_args = self.get_store_param()
        warehouse_args = self.get_warehouse_param(company_for_glow)
        order_list_params = get_order_list_param(order_list)
        url = 'https://%s.api.goflow.com/v1/orders?filters[status]=%s&%s' % (goflow_subdomain, str(goflow_state), str(order_list_params))
        # print('url',url)
        if store_args:
            url = url.rstrip()
            url += '&' + store_args
        if warehouse_args:
            url = url.rstrip()
            url += '&' + warehouse_args
        return url

    def _split_batch(self, ids):
        batch_size = 100
        for batch in tools.split_every(batch_size, ids):
            yield batch

    def _split_batch_100(self, ids):
        batch_size = 100
        for batch in tools.split_every(batch_size, ids):
            yield batch

    def insert_update_api_order(self, order, company_for_glow):
        # print(i)
        return_order_id = False
        goflow_store_id = order["store"]["id"]
        goflow_store_obj = self.env['goflow.store'].search([('goflow_id', '=', goflow_store_id)], limit=1)
        goflow_store_obj_partner_id, goflow_store_obj_id = goflow_store_obj.partner_id.id, goflow_store_obj.id

        # vals_partner_ship = self._prepare_partner_values(order)
        # partner_ship_obj = self.env['res.partner'].search([('name', '=', vals_partner_ship['name'])], limit=1)
        # if not partner_ship_obj:
        #     partner_ship_obj = self.env['res.partner'].create(vals_partner_ship)
        #     partner_ship_obj.parent_id = goflow_store_obj_partner_id
        order_lines = order["lines"]
        goflow_id = order["id"]
        # goflow_ship_boxes = order["shipment"]["boxes"]
        goflow_warehouse_id = order["warehouse"]["id"]
        goflow_warehouse_name = order["warehouse"]["name"]
        warehouse_obj = self.env['stock.warehouse'].search([('goflow_id', '=', goflow_warehouse_id)], limit=1)
        if not warehouse_obj:
            warehouse_obj = self.env['stock.warehouse'].create(
                {'name': goflow_warehouse_name, 'goflow_id': goflow_warehouse_id,
                 'code': goflow_warehouse_name[:2],
                 'company_id': company_for_glow and company_for_glow.id or False, 'sync_orders': True})
        warehouse_obj_id = warehouse_obj.id
        tracking_line_list = []
        check_if_order_exists = self.search([('goflow_id', '=', goflow_id)], limit=1)
        _logger.info("------------GO FLOW ORDER ID--------------------")
        _logger.info(goflow_id)
        goflow_id
        # print('check_if_order_exists', check_if_order_exists)
        order_array = order

        print("Processing order# %s | Date: %s" % (order["order_number"], order["date"]))

        if check_if_order_exists:
            order = check_if_order_exists
            # if order.warehouse_id != warehouse_obj:
            #     order.action_cancel()
            #     order.action_draft()
            #     order.warehouse_id = warehouse_obj_id
            #     order.action_confirm()
            order.write(self._prepare_edit_order_values(order_array))
            # order_ids.append(order.id)
            return_order_id = order.id

            for line in tracking_line_list:
                goflow_line_id = line['order_line_id']
                line_obj = self.env['sale.order.line'].search([('goflow_id', '=', goflow_line_id)], limit=1)
                if line_obj:
                    line_obj.goflow_tracking_number = line['tracking_number']

        if not check_if_order_exists:
            order_values = self._prepare_order_values(order, company_for_glow, warehouse_obj_id)
            so = self.env['sale.order'].create(order_values)
            so.partner_id = goflow_store_obj_partner_id
            so.partner_invoice_id = goflow_store_obj_partner_id
            so.partner_shipping_id = goflow_store_obj_partner_id
            so.goflow_id = order["id"]
            so.goflow_store_id = goflow_store_obj_id
            # so.company_id = company_for_glow and company_for_glow.id or False
            so.warehouse_id = warehouse_obj_id
            # order_ids.append(so.id)
            return_order_id = so.id
            for line in order_lines:
                _logger.info("--------------------------------")
                _logger.info(line)
                self.env['sale.order.line'].create(self._prepare_order_lines(line, so, tracking_line_list,
                                                                             company_for_glow))
            self.update_shipped_so_order_status(so)

        return return_order_id

    def sync_so_goflow(self, lastcall, goflow_state, date_range, update_sync_index=False):

        company_for_glow = self.env['res.company'].search([('use_for_goflow_api', '=', True)], limit=1)
        goflow_token = self.env['ir.config_parameter'].get_param('delivery_goflow.token_goflow')
        # goflow_cutoff_date = self.env['ir.config_parameter'].get_param('delivery_goflow.goflow_cutoff_date')
        headers = {
            'X-Beta-Contact': self.env.user.partner_id.email
        }
        url = self._preparing_url(lastcall, date_range, company_for_glow, goflow_state)
        result = requests.get(url, auth=BearerAuth(goflow_token), headers=headers, verify=True)
        # print(result.json())
        goflow_api = result.json()
        orders = goflow_api["data"]
        whileCounter = 1
        while goflow_api["next"]:
            # print("whileCounter:",whileCounter)
            goflow_api = requests.get(goflow_api["next"], auth=BearerAuth(goflow_token), headers=headers).json()
            orders.extend(goflow_api["data"])
            whileCounter = whileCounter + 1
        # print(len(orders))
        i = 1
        for batch_ids in self._split_batch(orders):
            order_ids = []
            for order in batch_ids:
                i += 1
                # print(i)
                order = self.insert_update_api_order(order, company_for_glow)
                if order:
                    order_ids.append(order)

            self.env.cr.commit()
            if order_ids and update_sync_index:
                self.env['goflow.sync.index'].sudo().create({'name': goflow_state, 'order_ids': order_ids})

    def sync_so_goflow_specific_orders(self, order_list, goflow_state):
        order_ids = []
        company_for_glow = self.env['res.company'].search([('use_for_goflow_api', '=', True)], limit=1)
        goflow_token = self.env['ir.config_parameter'].get_param('delivery_goflow.token_goflow')
        # goflow_cutoff_date = self.env['ir.config_parameter'].get_param('delivery_goflow.goflow_cutoff_date')
        headers = {
            'X-Beta-Contact': self.env.user.partner_id.email
        }
        for chunk_list in self._split_batch_100(order_list):
            url = self._preparing_url_specific_orders(company_for_glow, goflow_state, chunk_list)
            result = requests.get(url, auth=BearerAuth(goflow_token), headers=headers, verify=True)
            # print(result.json())
            goflow_api = result.json()
            orders = goflow_api["data"]
            whileCounter = 1
            while goflow_api["next"]:
                # print("whileCounter:",whileCounter)
                goflow_api = requests.get(goflow_api["next"], auth=BearerAuth(goflow_token), headers=headers).json()
                orders.extend(goflow_api["data"])
                whileCounter = whileCounter + 1
            # print(len(orders))
            i = 1
            for batch_ids in self._split_batch(orders):
                for order in batch_ids:
                    i += 1
                    order = self.insert_update_api_order(order, company_for_glow)
                    if order:
                        order_ids.append(order)
                self.env.cr.commit()
                if order_ids:
                    self.env['goflow.sync.index'].sudo().create({'name': goflow_state, 'order_ids': order_ids})
        return order_ids

    def sync_update_so_goflow(self, lastcall, goflow_state, date_range, update_sync_index=False, orders=False):

        company_for_glow = self.env['res.company'].search([('use_for_goflow_api', '=', True)], limit=1)
        goflow_token = self.env['ir.config_parameter'].get_param('delivery_goflow.token_goflow')
        # goflow_cutoff_date = self.env['ir.config_parameter'].get_param('delivery_goflow.goflow_cutoff_date')
        headers = {
            'X-Beta-Contact': self.env.user.partner_id.email
        }
        order_params = self._prepare_order_parameter(company_for_glow, orders)
        url = self._preparing_url_by_orders(company_for_glow, order_params)
        result = requests.get(url, auth=BearerAuth(goflow_token), headers=headers, verify=True)
        # print(result.json())
        goflow_api = result.json()
        orders = goflow_api["data"]
        whileCounter = 1
        while goflow_api["next"]:
            # print("whileCounter:",whileCounter)
            goflow_api = requests.get(goflow_api["next"], auth=BearerAuth(goflow_token), headers=headers).json()
            orders.extend(goflow_api["data"])
            whileCounter = whileCounter + 1
        # print(len(orders))
        i = 1
        for batch_ids in self._split_batch(orders):
            order_ids = []
            for order in batch_ids:
                i += 1
                # print(i)
                goflow_store_id = order["store"]["id"]
                goflow_store_obj = self.env['goflow.store'].search([('goflow_id', '=', goflow_store_id)], limit=1)
                goflow_store_obj_partner_id, goflow_store_obj_id = goflow_store_obj.partner_id.id, goflow_store_obj.id

                vals_partner_ship = self._prepare_partner_values(order)
                # partner_ship_obj = self.env['res.partner'].search([('name', '=', vals_partner_ship['name'])], limit=1)
                # if not partner_ship_obj:
                #     partner_ship_obj = self.env['res.partner'].create(vals_partner_ship)
                #     partner_ship_obj.parent_id = goflow_store_obj_partner_id
                order_lines = order["lines"]
                goflow_id = order["id"]
                # goflow_ship_boxes = order["shipment"]["boxes"]
                goflow_warehouse_id = order["warehouse"]["id"]
                goflow_warehouse_name = order["warehouse"]["name"]
                warehouse_obj = self.env['stock.warehouse'].search([('goflow_id', '=', goflow_warehouse_id)], limit=1)
                if not warehouse_obj:
                    warehouse_obj = self.env['stock.warehouse'].create(
                        {'name': goflow_warehouse_name, 'goflow_id': goflow_warehouse_id,
                         'code': goflow_warehouse_name[:2],
                         'company_id': company_for_glow and company_for_glow.id or False, 'sync_orders': True})
                warehouse_obj_id = warehouse_obj.id
                tracking_line_list = []
                check_if_order_exists = self.search([('goflow_id', '=', goflow_id)], limit=1)
                # print('check_if_order_exists', check_if_order_exists)
                order_array = order

                print("Processing order# %s | Date: %s" % (order["order_number"], order["date"]))

                if check_if_order_exists:
                    order = check_if_order_exists
                    # if order.warehouse_id != warehouse_obj:
                    #     order.action_cancel()
                    #     order.action_draft()
                    #     order.warehouse_id = warehouse_obj_id
                    #     order.action_confirm()
                    order.write(self._prepare_edit_order_values(order_array))
                    order_ids.append(order.id)

                    for line in tracking_line_list:
                        goflow_line_id = line['order_line_id']
                        line_obj = self.env['sale.order.line'].search([('goflow_id', '=', goflow_line_id)], limit=1)
                        if line_obj:
                            line_obj.goflow_tracking_number = line['tracking_number']

            self.env.cr.commit()
            if order_ids:
                self.env['goflow.sync.index'].sudo().create({'name': goflow_state, 'order_ids': order_ids})

    @api.constrains('goflow_store_latest_ship')
    def _goflow_store_latest_ship(self):
        for record in self:
            record.write({'commitment_date': record.goflow_store_latest_ship})
