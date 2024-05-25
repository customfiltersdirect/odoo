from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class ProductReplenish(models.TransientModel):
    _name = 'product.replenish.wizard'
    _description = 'Product Replenish Wizard'

    product_ids = fields.Many2many('product.product', string='Product')
    quantity = fields.Float('Quantity', default=1, required=True)
    date_planned = fields.Datetime('Scheduled Date', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unity of measure')
    product_uom_category_id = fields.Many2one('uom.category', related='product_ids.uom_id.category_id', readonly=True)
    route_ids = fields.Many2many(
        'stock.location.route', string='Preferred Routes',
        help="Apply specific route(s) for the replenishment instead of product's default routes.")
    company_id = fields.Many2one('res.company')
    product_has_variants = fields.Boolean('Has variants')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')

    def show_dialog(self, message):
        action = self.env["ir.actions.act_window"].warning(
            title=_("Information"),
            message=message,
            close_on_confirm=True,
        )
        return action

    def launch_replenishment(self):
        errors = []
        for product_id in self.product_ids:
            try:
                uom_reference = product_id.uom_id
                self.quantity = self.product_uom_id._compute_quantity(self.quantity, uom_reference)
                self.env['procurement.group'].with_context(clean_context(self.env.context)).run([
                    self.env['procurement.group'].Procurement(
                        product_id,
                        self.quantity,
                        uom_reference,
                        self.warehouse_id.lot_stock_id,
                        _("Manual Replenishment"),
                        _("Manual Replenishment"),
                        self.warehouse_id.company_id,
                        self._prepare_run_values()
                    )
                ])
            except UserError as error:
                errors.append(str(error))
        print("These are error", errors)
        if errors:
            raise UserError(errors)

    def _prepare_run_values(self):
        replenishment = self.env['procurement.group'].create({})
        values = {
            'warehouse_id': self.warehouse_id,
            'route_ids': self.route_ids,
            'date_planned': self.date_planned,
            'group_id': replenishment,
        }
        return values