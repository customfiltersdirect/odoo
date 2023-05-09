from odoo import api, fields, models, _


class GoflowOrderSyncDate(models.TransientModel):
    _name = "goflow.order.sync.date"
    _description = "Sale Order Sync Goflow Using Dates"

    use_last_sync_date = fields.Boolean(string='Use last sync date', default=True)
    last_sync_date = fields.Date('Last sync date', compute="_compute_last_sync_date")

    sync_mode = fields.Selection([('shipped', 'shipped'),
                             ('in_packing', 'in_packing'),
                             ('ready_to_pick', 'ready_to_pick'),
                             ('in_picking', 'in_picking')], required=True)
    from_date = fields.Date('From', default=fields.Date.context_today)
    to_date = fields.Date('To', default=fields.Date.context_today)

    @api.depends('sync_mode')
    def _compute_last_sync_date(self):
        icp = self.env['ir.config_parameter'].sudo()
        last_inpicking_sync_str = icp.get_param('delivery_goflow.last_inpicking_sync')
        last_shipped_sync_str = icp.get_param('delivery_goflow.last_shipped_sync')
        last_readytopick_sync_str = icp.get_param('delivery_goflow.last_readytopick_sync')

        for rec in self:
            if rec.sync_mode == 'shipped':
                rec.last_sync_date = last_shipped_sync_str
            elif rec.sync_mode == 'ready_to_pick':
                rec.last_sync_date = last_readytopick_sync_str
            elif rec.sync_mode == 'in_picking':
                rec.last_sync_date = last_inpicking_sync_str
            else:
                rec.last_sync_date = False

    def action_sync_now(self):
        date_range = False
        if not self.use_last_sync_date:
            date_range = {
                'date_from': self.from_date,
                'date_to': self.to_date,
            }
        if self.sync_mode == 'shipped':
            self.env['sale.order'].sudo().api_call_for_sync_orders_shipped(call_for_index=True, date_range=date_range)
        elif self.sync_mode == 'ready_to_pick':
            self.env['sale.order'].sudo().api_call_for_sync_orders_ready_to_pick(call_for_index=True, date_range=date_range)
        else:
            self.env['sale.order'].sudo().api_call_for_sync_orders_in_picking(call_for_index=True, date_range=date_range)