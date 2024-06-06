import logging
from datetime import date
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo import api, fields, models, _, exceptions

class MRP_Production(models.Model):
    _inherit = 'mrp.production'

    transfer_count = fields.Integer(compute='compute_count')

    def compute_count(self):
        for record in self:
            record.transfer_count = self.env['stock.picking'].search_count(
                [('production_order', '=', self.id)])

    def Create_Transfer_from_MO(self):
        lines = []
        for rec in self:
            lines.append((0,0,{
                'product_id' : rec.product_id.id,
                'location_id': self.location_dest_id.id,
                'location_dest_id' : self.location_dest_id.id,
                'quantity': rec.qty_producing,
            }))
            obj = {
                'picking_type_id' : 142,
                'location_id' : self.location_dest_id.id,
                'location_dest_id': self.location_dest_id.id,
                'origin': rec.id,
                'production_order': rec.id,
                'move_line_ids_without_package' : lines
            }

        check_for_existing_picking = self.env['stock.picking'].search([('production_order','=',self.id)])
        if not check_for_existing_picking:
            mrp = self.env['stock.picking'].create(obj)
            mrp.action_confirm()
            mrp.button_validate()
    

    def button_mark_done(self):
        self.Create_Transfer_from_MO()
        res = self.pre_button_mark_done()
        if res is not True:
            return res

        if self.env.context.get('mo_ids_to_backorder'):
            productions_to_backorder = self.browse(self.env.context['mo_ids_to_backorder'])
            productions_not_to_backorder = self - productions_to_backorder
        else:
            productions_not_to_backorder = self
            productions_to_backorder = self.env['mrp.production']

        self.workorder_ids.button_finish()

        backorders = productions_to_backorder and productions_to_backorder._split_productions()
        backorders = backorders - productions_to_backorder

        productions_not_to_backorder._post_inventory(cancel_backorder=True)
        productions_to_backorder._post_inventory(cancel_backorder=True)

        # if completed products make other confirmed/partially_available moves available, assign them
        done_move_finished_ids = (productions_to_backorder.move_finished_ids | productions_not_to_backorder.move_finished_ids).filtered(lambda m: m.state == 'done')
        done_move_finished_ids._trigger_assign()

        # Moves without quantity done are not posted => set them as done instead of canceling. In
        # case the user edits the MO later on and sets some consumed quantity on those, we do not
        # want the move lines to be canceled.
        (productions_not_to_backorder.move_raw_ids | productions_not_to_backorder.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel')).write({
            'state': 'done',
            'product_uom_qty': 0.0,
        })
        for production in self:
            production.write({
                'date_finished': fields.Datetime.now(),
                'priority': '0',
                'is_locked': True,
                'state': 'done',
            })

        report_actions = self._get_autoprint_done_report_actions()
        if self.env.context.get('skip_redirection'):
            if report_actions:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'do_multi_print',
                    'context': {},
                    'params': {
                        'reports': report_actions,
                    }
                }
            return True
        another_action = False
        if not backorders:
            if self.env.context.get('from_workorder'):
                another_action = {
                    'type': 'ir.actions.act_window',
                    'res_model': 'mrp.production',
                    'views': [[self.env.ref('mrp.mrp_production_form_view').id, 'form']],
                    'res_id': self.id,
                    'target': 'main',
                }
            elif self.user_has_groups('mrp.group_mrp_reception_report'):
                mos_to_show = self.filtered(lambda mo: mo.picking_type_id.auto_show_reception_report)
                lines = mos_to_show.move_finished_ids.filtered(lambda m: m.product_id.type == 'product' and m.state != 'cancel' and m.picked and not m.move_dest_ids)
                if lines:
                    if any(mo.show_allocation for mo in mos_to_show):
                        another_action = mos_to_show.action_view_reception_report()
            if report_actions:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'do_multi_print',
                    'params': {
                        'reports': report_actions,
                        'anotherAction': another_action,
                    }
                }
            if another_action:
                return another_action
            return True
        context = self.env.context.copy()
        context = {k: v for k, v in context.items() if not k.startswith('default_')}
        for k, v in context.items():
            if k.startswith('skip_'):
                context[k] = False
        another_action = {
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
            'context': dict(context, mo_ids_to_backorder=None)
        }
        if len(backorders) == 1:
            another_action.update({
                'views': [[False, 'form']],
                'view_mode': 'form',
                'res_id': backorders[0].id,
            })
        else:
            another_action.update({
                'name': _("Backorder MO"),
                'domain': [('id', 'in', backorders.ids)],
                'views': [[False, 'list'], [False, 'form']],
                'view_mode': 'tree,form',
            })
        if report_actions:
            return {
                'type': 'ir.actions.client',
                'tag': 'do_multi_print',
                'params': {
                    'reports': report_actions,
                    'anotherAction': another_action,
                }
            }
        return another_action
    
    def get_piap_transfers(self):
        self.ensure_one()
        return {
            'name': 'Put In a Pack',
            'domain': [('production_order', '=', self.name)],
            'view_type': 'form',
            'res_model': 'stock.picking',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    production_order = fields.Many2one('mrp.production' , string='Manufacturing Order')