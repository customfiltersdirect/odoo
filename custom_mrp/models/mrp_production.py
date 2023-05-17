from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_cancel(self):
        res = super(MrpProduction, self).action_cancel()
        for production in self:
            po_id = production.procurement_group_id.stock_move_ids.created_purchase_line_id.order_id | production.procurement_group_id.stock_move_ids.move_orig_ids.purchase_line_id.order_id
            if po_id:
                po_id.button_cancel()

        return res