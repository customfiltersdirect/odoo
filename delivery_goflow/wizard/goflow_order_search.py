from odoo import api, fields, models, _

class GoflowOrderSearchWizard(models.TransientModel):
    _name = "goflow.order.search.wizard"
    _description = "Sale Order Api Wizard By Internal ID"
    goflow_invoice_number = fields.Text()
    not_found = fields.Text()
    show_continue_button = fields.Boolean(string='Show Continue Anyway Button', default=False)
    found_invoices_data = fields.Text()


    def action_search_goflow_orders(self):
        if self.goflow_invoice_number:
            goflow_list=set(self.goflow_invoice_number.split())
            # invoice_records = self.env['account.move'].search([]).filtered(lambda r: r.goflow_invoice_no).mapped('goflow_invoice_no')
            found_goflow=self.env['account.move'].search([('goflow_invoice_no', 'in', self.goflow_invoice_number.split())])
            self.found_invoices_data = found_goflow.ids

            not_found= list(goflow_list - set(found_goflow.mapped('goflow_invoice_no')))
            if not_found:
                self.show_continue_button=True
                self.not_found = ', '.join(not_found)
                action = {
                    'name': 'Goflow Invoices',
                    'type': 'ir.actions.act_window',
                    'res_model': 'goflow.order.search.wizard',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_id': self.id,
                    'target': 'new'
                }
                return action
            else:
                action = self.env.ref('account.action_move_out_invoice_type').read()[0]
                action['domain'] = [('id', 'in', self.found_invoices_data.split('[')[1].split(']')[0].split(','))]
                action['context'] = {}
                # action['views'] = [(self.env.ref('account.view_out_invoice_tree').id, 'tree')]
                action['display_name'] = _('Goflow Invoices')

                return action

    def action_continue_anyway(self):

        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['domain'] = [('id', 'in', self.found_invoices_data.split('[')[1].split(']')[0].split(','))]
        action['context'] = {}
        # action['views'] = [(self.env.ref('account.view_out_invoice_tree').id, 'tree')]
        action['display_name'] = _('Goflow Invoices')

        return action