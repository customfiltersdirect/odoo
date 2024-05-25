# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class PrintNodeReportPolicy(models.Model):
    """ Call Button
    """
    _name = 'printnode.report.policy'
    _description = 'PrintNode Report Policy'

    _rec_name = 'report_id'

    report_id = fields.Many2one(
        'ir.actions.report',
        string='Report',
        required=True,
        domain="[('report_type', 'in', ('qweb-pdf', 'qweb-text', 'py3o'))]",
    )

    report_model = fields.Char(
        related='report_id.model',
        readonly=True,
    )

    report_type = fields.Selection(
        related='report_id.report_type',
        readonly=True,
    )

    printer_id = fields.Many2one(
        'printnode.printer',
        string='Printer',
        ondelete='set null',
    )

    printer_bin = fields.Many2one(
        'printnode.printer.bin',
        string='Printer Bin',
        domain='[("printer_id", "=", printer_id)]',
    )

    report_paper_id = fields.Many2one(
        'printnode.paper',
        string='Report Paper'
    )

    exclude_from_auto_printing = fields.Boolean(
        'Exclude from Auto-printing', default=False,
        help="""If you would like to exclude this report from auto-printing,
                select this checkbox."""
    )

    error = fields.Boolean(
        compute='_compute_print_rules',
    )

    notes = fields.Html(
        string='Note',
        compute='_compute_print_rules',
    )

    _sql_constraints = [
        (
            'report_id',
            'unique(report_id)',
            'Report policy is unique for report.'
        ),
    ]

    @api.depends('report_paper_id', 'exclude_from_auto_printing')
    def _compute_print_rules(self):

        def _html(message, icon='fa fa-question-circle-o'):
            return f'<span class="{icon}" title="{message}"></span>'

        def _ok(message):
            return False, _html(message, 'fa fa-circle-o')

        def _error(message):
            return True, _html(message, 'fa fa-exclamation-circle')

        for report in self:
            if report.exclude_from_auto_printing:
                report.error, report.notes = _ok(_('Configuration is valid.'))
                continue

            printers = self.env['printnode.rule'].search([
                ('report_id', '=', report.report_id.id)
            ]).mapped('printer_id')

            printers |= report.printer_id

            errors = list(set(filter(None, [
                printer.printnode_check_report(report.report_id, False)
                for printer in printers
            ])))

            if errors:
                report.error, report.notes = _error('\n'.join(errors))
            else:
                report.error, report.notes = _ok(_('Configuration is valid.'))

    @api.onchange('printer_id')
    def _onchange_printer(self):
        """
        Reset printer_bin field to avoid bug with printing
        in wrong bin
        """
        self.printer_bin = self.printer_id.default_printer_bin.id
