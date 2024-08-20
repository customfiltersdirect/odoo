from odoo import fields, models, api


class StockSale(models.Model):
    _name = 'sale.stock.report'
    # _inherit = 'sale.report'
    _description = "Stock Sale Report"
    _auto = False
    _rec_name = 'product_id'
    _order = 'product_id asc'

    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    bb = fields.Float(string="BB&EXT", readonly=True)
    on_hand = fields.Float(string="On Hand", readonly=True)
    difference = fields.Float(string="Difference", readonly=True)
    difference_status = fields.Char(string="Difference Status", readonly=True)

    date_order = fields.Date(string="Order Date", readonly=True)


    # date_from = fields.Date(string="From Date")
    # date_to = fields.Date(string="To Date")


    @api.model
    def init(self):
        self.env.cr.execute("DROP VIEW IF EXISTS sale_stock_report CASCADE")

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW sale_stock_report AS (
                SELECT
                    l.product_id AS product_id,  
                    SUM(l.product_uom_qty) AS bb,  
                    COALESCE(SQ.quantity, 0) AS on_hand,  
                    COALESCE(SQ.quantity,0) - SUM(l.product_uom_qty) AS difference,
                    CASE
                        WHEN COALESCE(SQ.quantity, 0) - SUM(l.product_uom_qty) > 0 THEN 'OK'
                        ELSE 'SHORT'
                    END AS difference_status,
                    so.date_order AS date_order
                FROM
                    sale_order_line l   
                JOIN
                    sale_order so ON l.order_id = so.id
                JOIN
                    stock_picking sp ON so.id = sp.sale_id
                LEFT JOIN (
                    SELECT 
                        sq.product_id, 
                        SUM(sq.quantity) AS quantity  
                    FROM 
                        stock_quant sq
                    JOIN 
                        stock_location sl ON sq.location_id = sl.id
                    WHERE 
                        sl.usage = 'internal' 
                    GROUP BY 
                        sq.product_id 
                ) AS SQ ON l.product_id = SQ.product_id
                WHERE
                    l.display_type IS NULL 
                    AND so.state NOT IN ('done', 'cancel')
                    AND sp.state NOT IN ('done', 'cancel')
                GROUP BY
                    l.product_id, SQ.quantity, so.date_order
                    
            )
        """)

    @api.model
    def _get_done_states(self):
        return ['sale']

