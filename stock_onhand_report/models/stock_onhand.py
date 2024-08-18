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
    END AS difference_status
        FROM
            sale_order_line l
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
        GROUP BY
            l.product_id, SQ.quantity

            )
        """)


    @api.model
    def _get_done_states(self):
        return ['sale']

    # Additional fields
    filter_difference = fields.Char(string="Filter Difference", readonly=True)
    foh = fields.Char(string="FOH", readonly=True)
    need = fields.Char(string="Need", readonly=True)
    short_or_ok_for_filter_difference = fields.Char(string="Short or OK for Filter Difference", readonly=True)

    #
    # def _with_sale(self):
    #     return ""
    #
    # def _select_sale(self):
    #     select_ = f"""
    #         MIN(l.id) AS id,
    #         l.product_id AS product_id,
    #         t.uom_id AS product_uom,
    #         CASE WHEN l.product_id IS NOT NULL THEN SUM(l.product_uom_qty / u.factor * u2.factor) ELSE 0 END AS product_uom_qty,
    #         CASE WHEN l.product_id IS NOT NULL THEN SUM(l.qty_delivered / u.factor * u2.factor) ELSE 0 END AS qty_delivered,
    #         CASE WHEN l.product_id IS NOT NULL THEN SUM((l.product_uom_qty - l.qty_delivered) / u.factor * u2.factor) ELSE 0 END AS qty_to_deliver,
    #         CASE WHEN l.product_id IS NOT NULL THEN SUM(l.qty_invoiced / u.factor * u2.factor) ELSE 0 END AS qty_invoiced,
    #         CASE WHEN l.product_id IS NOT NULL THEN SUM(l.qty_to_invoice / u.factor * u2.factor) ELSE 0 END AS qty_to_invoice,
    #         CASE WHEN l.product_id IS NOT NULL THEN SUM(l.price_total
    #             / {self._case_value_or_one('s.currency_rate')}
    #             * {self._case_value_or_one('currency_table.rate')}
    #             ) ELSE 0
    #         END AS price_total,
    #         CASE WHEN l.product_id IS NOT NULL THEN SUM(l.price_subtotal
    #             / {self._case_value_or_one('s.currency_rate')}
    #             * {self._case_value_or_one('currency_table.rate')}
    #             ) ELSE 0
    #         END AS price_subtotal,
    #         CASE WHEN l.product_id IS NOT NULL THEN SUM(l.untaxed_amount_to_invoice
    #             / {self._case_value_or_one('s.currency_rate')}
    #             * {self._case_value_or_one('currency_table.rate')}
    #             ) ELSE 0
    #         END AS untaxed_amount_to_invoice,
    #         CASE WHEN l.product_id IS NOT NULL THEN SUM(l.untaxed_amount_invoiced
    #             / {self._case_value_or_one('s.currency_rate')}
    #             * {self._case_value_or_one('currency_table.rate')}
    #             ) ELSE 0
    #         END AS untaxed_amount_invoiced,
    #         COUNT(*) AS nbr,
    #         s.name AS name,
    #         s.date_order AS date,
    #         s.state AS state,
    #         s.invoice_status as invoice_status,
    #         s.partner_id AS partner_id,
    #         s.user_id AS user_id,
    #         s.company_id AS company_id,
    #         s.campaign_id AS campaign_id,
    #         s.medium_id AS medium_id,
    #         s.source_id AS source_id,
    #         t.categ_id AS categ_id,
    #         s.pricelist_id AS pricelist_id,
    #         s.analytic_account_id AS analytic_account_id,
    #         s.team_id AS team_id,
    #         p.product_tmpl_id,
    #         partner.commercial_partner_id AS commercial_partner_id,
    #         partner.country_id AS country_id,
    #         partner.industry_id AS industry_id,
    #         partner.state_id AS state_id,
    #         partner.zip AS partner_zip,
    #         CASE WHEN l.product_id IS NOT NULL THEN SUM(p.weight * l.product_uom_qty / u.factor * u2.factor) ELSE 0 END AS weight,
    #         CASE WHEN l.product_id IS NOT NULL THEN SUM(p.volume * l.product_uom_qty / u.factor * u2.factor) ELSE 0 END AS volume,
    #         l.discount AS discount,
    #         CASE WHEN l.product_id IS NOT NULL THEN SUM(l.price_unit * l.product_uom_qty * l.discount / 100.0
    #             / {self._case_value_or_one('s.currency_rate')}
    #             * {self._case_value_or_one('currency_table.rate')}
    #             ) ELSE 0
    #         END AS discount_amount,
    #         concat('sale.order', ',', s.id) AS order_reference"""
    #
    #     additional_fields_info = self._select_additional_fields()
    #     template = """,
    #         %s AS %s"""
    #     for fname, query_info in additional_fields_info.items():
    #         select_ += template % (query_info, fname)
    #
    #     return select_
    #
    # def _case_value_or_one(self, value):
    #     return f"""CASE COALESCE({value}, 0) WHEN 0 THEN 1.0 ELSE {value} END"""
    #
    # def _select_additional_fields(self):
    #     """Hook to return additional fields SQL specification for select part of the table query.
    #
    #     :returns: mapping field -> SQL computation of field, will be converted to '_ AS _field' in the final table definition
    #     :rtype: dict
    #     """
    #     return {}
    #
    # def _from_sale(self):
    #     return """
    #         sale_order_line l
    #         LEFT JOIN sale_order s ON s.id=l.order_id
    #         JOIN res_partner partner ON s.partner_id = partner.id
    #         LEFT JOIN product_product p ON l.product_id=p.id
    #         LEFT JOIN product_template t ON p.product_tmpl_id=t.id
    #         LEFT JOIN uom_uom u ON u.id=l.product_uom
    #         LEFT JOIN uom_uom u2 ON u2.id=t.uom_id
    #         JOIN {currency_table} ON currency_table.company_id = s.company_id
    #         """.format(
    #         currency_table=self.env['res.currency']._get_query_currency_table(self.env.companies.ids, fields.Date.today())
    #         )
    #
    # def _where_sale(self):
    #     return """
    #         l.display_type IS NULL"""
    #
    # def _group_by_sale(self):
    #     return """
    #         l.product_id,
    #         l.order_id,
    #         t.uom_id,
    #         t.categ_id,
    #         s.name,
    #         s.date_order,
    #         s.partner_id,
    #         s.user_id,
    #         s.state,
    #         s.invoice_status,
    #         s.company_id,
    #         s.campaign_id,
    #         s.medium_id,
    #         s.source_id,
    #         s.pricelist_id,
    #         s.analytic_account_id,
    #         s.team_id,
    #         p.product_tmpl_id,
    #         partner.commercial_partner_id,
    #         partner.country_id,
    #         partner.industry_id,
    #         partner.state_id,
    #         partner.zip,
    #         l.discount,
    #         s.id,
    #         currency_table.rate"""
    #
    # def _query(self):
    #     with_ = self._with_sale()
    #     return f"""
    #         {"WITH" + with_ + "(" if with_ else ""}
    #         SELECT {self._select_sale()}
    #         FROM {self._from_sale()}
    #         WHERE {self._where_sale()}
    #         GROUP BY {self._group_by_sale()}
    #         {")" if with_ else ""}
    #     """
    #
    # @property
    # def _table_query(self):
    #     return self._query()
    #
    #
    #
