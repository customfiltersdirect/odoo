from odoo import models, fields

class DateRangeWizard(models.TransientModel):
    _name = 'date.range.wizard'
    _description = 'Date Range Wizard'

    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)

    def confirm_btn(self):
        domain = []

        if self.date_from and self.date_to:
            domain = [('date_deadline', '>=', self.date_from), ('date_deadline', '<=', self.date_to)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Stock Sale Report',
            'res_model': 'sale.stock.report',
            'view_mode': 'pivot',  # Change to the desired view mode
            'target': 'current',
            'domain': domain,  # Filter the records based on the selected date range
        }