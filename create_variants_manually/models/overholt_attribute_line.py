from odoo import fields, models, api, _

class OverholtAttributeLine(models.Model):
    _name = "overholt.attribute.line"
    _description = "Overholt Attribute Lines"

    attribute_id = fields.Many2one(
        comodel_name='product.attribute',
        string="Attribute",
        ondelete='cascade',
        required=True,
        index=True)
    value_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        string="Values",
        domain="[('attribute_id', '=', attribute_id)]",
        ondelete='cascade')
    match_all = fields.Boolean(copy=False)

