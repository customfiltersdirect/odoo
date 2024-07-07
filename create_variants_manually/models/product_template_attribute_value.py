from odoo import fields, models, api, _

class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    exclude_for = fields.One2many(
        comodel_name='product.template.attribute.exclusion',
        inverse_name='product_template_attribute_value_id',
        string="Exclude for",
        help="Make this attribute value not compatible with "
             "other values of the product or some attribute values of optional and accessory products.", copy=True)

    def _get_combination_name(self):
        """Exclude values from single value lines attributes."""
        ptavs = self.with_prefetch(self._prefetch_ids)
        ptavs = ptavs._filter_single_value_lines().with_prefetch(self._prefetch_ids)
        return ", ".join([ptav.name for ptav in ptavs])