# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PrintnodePrintSaleOrderLineReportsWizard(models.TransientModel):
    _name = 'printnode.print.sale.order.line.reports.wizard'
    _inherit = 'printnode.abstract.print.line.reports.wizard'
    _description = 'Print sale.order.line Reports Wizard'

    record_line_ids = fields.One2many(
        comodel_name='printnode.print.sale.order.line.reports.wizard.line',
        inverse_name='wizard_id',
        string='Records',
        default=lambda self: self._default_record_line_ids(),
    )

    def _get_report_domain(self):
        return [
            ('model', '=', 'sale.order.line'),
            ('report_type', 'in', ['qweb-pdf', 'qweb-text', 'py3o']),
        ]

    def _default_record_line_ids(self):
        sale_order_id = self.env['sale.order'].browse(self.env.context.get('active_id'))

        record_ids = sale_order_id.order_line

        return [
            (0, 0, {
                'record_id': rec.id,
                'name': rec.product_id.name,
                'quantity': rec.product_uom_qty
            })
            for rec in record_ids
        ]

    def _get_line_model(self):
        return self.env['sale.order.line']


class PrintnodePrintStockMoveReportsWizardLine(models.TransientModel):
    _name = 'printnode.print.sale.order.line.reports.wizard.line'
    _inherit = 'printnode.abstract.print.line.reports.wizard.line'
    _description = 'Record Line'

    record_id = fields.Many2one(
        comodel_name='sale.order.line',
    )

    name = fields.Char(
        string='Name',
        related='record_id.product_id.name',
    )

    wizard_id = fields.Many2one(
        comodel_name='printnode.print.sale.order.line.reports.wizard',
    )
