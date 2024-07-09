from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    # ASIN = fields.Char(string="ASIN")
    # go_flow_item_id = fields.Char(string='GO FLow Item ID')
    # go_flow_item_number = fields.Char(string='GO Flow Item Nummber')

    @api.constrains('goflow_id_var')
    def _goflow_id_var(self):
        if self.goflow_id_var != False:
            result = self.env['product.product'].search([('goflow_id_var', '=', self.goflow_id_var),('id', '!=', self.id)], limit=1)
            if result:
                match_rec = self.env['product.product'].search([('goflow_id_var', '=', self.goflow_id_var)], limit=1)
                raise ValidationError("The Operation cannot be completed: this Goflow ID has already assiigned to [" + str(match_rec.default_code) + "] [" + match_rec.name+ "]")

    @api.constrains('goflow_item_no_var')
    def _goflow_item_no_var(self):
        if self.goflow_id_var != False:
            result = self.env['product.product'].search([('goflow_item_no_var', '=', self.goflow_item_no_var),('id', '!=', self.id)], limit=1)
            if result:
                match_rec = self.env['product.product'].search([('goflow_item_no_var', '=', self.goflow_item_no_var)], limit=1)
                raise ValidationError("The Operation cannot be completed: this Goflow Item No has already assiigned to [" + str(match_rec.default_code) + "] [" + match_rec.name + "]")

    @api.constrains('asin_var')
    def _asin_var(self):
        if self.goflow_id_var != False:
            result = self.env['product.product'].search([('asin_var', '=', self.asin_var),('id', '!=', self.id)], limit=1)
            if result:
                match_rec = self.env['product.product'].search([('asin_var', '=', self.asin_var)], limit=1)
                raise ValidationError("The Operation cannot be completed: this Asin ID has already assiigned to [" + str(match_rec.default_code) + "] [" + match_rec.name+ "]")
