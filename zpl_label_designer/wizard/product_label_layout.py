from odoo import _, api, exceptions, fields, models


PRODUCT_LABEL_MODELS_MAPPING = {
    'product.template': 'product.template',
    'product.product': 'product.product',
    'stock.picking': 'product.product',
}


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    print_format = fields.Selection(
        selection_add=[('zld_label', 'Label From ZPL Designer')],
        ondelete={'zld_label': 'set default'}
    )

    zld_label_id = fields.Many2one(
        string='Available Labels from ZPL Designer',
        comodel_name='zld.label',
        domain="[('id', 'in', zld_label_ids)]",
    )

    # This field used as filter for zld_label_id field
    zld_label_ids = fields.Many2many(
        string='Label from ZPL Designer',
        comodel_name='zld.label',
        compute='_compute_zld_label_ids',
    )

    @api.depends('print_format')
    def _compute_zld_label_ids(self):
        for rec in self:
            # Update domain for zld_label_id field
            if self.print_format != 'zld_label':
                rec.zld_label_ids = False
                return

            active_model = ''
            if rec.product_tmpl_ids:
                active_model = 'product.template'
            elif rec.product_ids:
                active_model = 'product.product'

            rec.zld_label_ids = self.env['zld.label'].search([
                ('is_published', '=', True),
                ('model_id', '=', PRODUCT_LABEL_MODELS_MAPPING[active_model])
            ])

    def _prepare_report_data(self):
        xml_id, data = super()._prepare_report_data()

        if self.print_format == 'zld_label':
            if not self.zld_label_id:
                raise exceptions.UserError(_('Please select a ZPL Designer label'))

            xml_id = self.zld_label_id.action_report_id.xml_id

            # Mark the label as Product Label, so we will manually add docids later (check
            # 'ir.actions.report' model for details)
            data['is_zld_product_label'] = True

            return xml_id, data

        return xml_id, data
