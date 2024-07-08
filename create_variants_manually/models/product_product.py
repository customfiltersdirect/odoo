# Copyright 2015 Oihane Crucelaegui - AvanzOSC
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 ACSONE SA/NV
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import _, api, exceptions, models
from odoo.tools import config
from odoo import fields
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = "product.product"

    my_product_tmpl_id = fields.Many2one("product.template")

    # @api.onchange("my_product_tmpl_id")
    # def onchange_my_product_tmpl_id(self):
    #     if self.my_product_tmpl_id:
    #         self.name = self.my_product_tmpl_id.name

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(ProductProduct, self).create(vals_list)
    #     for product in res:
    #         if product.my_product_tmpl_id:
    #             last_template = product.product_tmpl_id
    #             product.product_tmpl_id = product.my_product_tmpl_id
    #             last_template.unlink()
    #     return res

    def action_unlink_and_do_nothing(self):
        if self.product_tmpl_id.product_variant_ids and len(self.product_tmpl_id.product_variant_ids) == 1:
            raise UserError("You cannot delete the first variant")
        if self.product_tmpl_id.product_variant_ids and self.product_tmpl_id.product_variant_ids.sorted(key="id")[0].id == self.id:
            raise UserError("You cannot delete the first variant")
        self.unlink()
        wizard_id = self.env.context.get("overholt_wizard_create_variants_id", False)
        return {
            "type": "ir.actions.act_window",
            "res_model": "create.variants.overholt",
            "res_id": wizard_id,
            "view_mode": "form",
            "target": "new"
        }