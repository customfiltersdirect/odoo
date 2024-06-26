from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    # ASIN = fields.Char(string="ASIN")
    # go_flow_item_id = fields.Char(string='GO FLow Item ID')
    # go_flow_item_number = fields.Char(string='GO Flow Item Nummber')
    _sql_constraints = [
        ('goflow_id_var_uniq', 'unique(goflow_id_var)', 'A go flow id can only be assigned to one product.'),
        ('goflow_item_no_var_uniq', 'unique(goflow_item_no_var)', 'A go flow item number can only be assigned to one product.'),
        ('asin_var_uniq', 'unique(asin_var)', 'A asin can only be assigned to one product.'),
    ]
