from odoo import models, fields, api, _
from odoo import tools


class KsInventoryValuation(models.Model):
    # _inherit = "product.product"
    _name = "inventory_board.ks_inventory"
    _description = "Custom Inventory"
    _auto = False
    _order = 'date desc'

    # product_id = fields.Integer('Product', readonly=True)
    product_id = fields.Many2one('product.product', 'Product Variant', readonly=True)
    quantity = fields.Float('Quantity', readonly=True)
    date = fields.Datetime('Date', readonly=True)
    total = fields.Float("Total Cost", readonly=True)

    _query = """select 
            q.id, q.product_id as product_id, q.company_id, q.location_id, q.quantity as quantity,  c.cost,
                q.quantity * c.cost as total, date_trunc('day',c.datetime) as date 
            from stock_quant q 
            inner join stock_location sl on sl.id = q.location_id 
            inner join c on c.product_id = q.product_id 
            where sl.usage = 'internal'
            """

    _with = """with c as (
                        select product_id, cost, datetime from product_price_history where id in (
                        select max(id) from product_price_history  group by product_id, date_trunc('day',datetime)))                                                           
            """


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s %s)""" %
                            (self._table, self._with, self._query))
