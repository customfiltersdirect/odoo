from odoo import models, fields, api


class work_order(models.Model):
    _inherit = 'mrp.workorder'

    attribute_values = fields.Char(string='Attribute Values', compute='_compute_attribute_values', store=True)

    # @api.depends('product_id')
    # def _compute_attribute_values(self):
    #     for rec in self:
    #         attribute_names = []
    #         if rec.product_id:
    #             for attribute in rec.product_id.product_template_variant_value_ids:
    #                 attribute_names.append(attribute.name)
    #         rec.attribute_values = ', '.join(attribute_names)

    @api.depends('product_id')
    def _compute_attribute_values(self):
        for rec in self:
            list_ = []
            list2 = []
            for attribute in rec.product_id.product_template_variant_value_ids:
                if 'Merv' in attribute.name:
                    list_.append(attribute.name)
                else:
                    list2.append(attribute.name)
            list_main = list_ + list2
            rec.attribute_values = ', '.join(list_main)