# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class PrintNodeRule(models.Model):
    """ Rule
    """
    _name = 'printnode.rule'
    _description = 'PrintNode Rule'

    active = fields.Boolean(
        'Active', default=True,
        help="""Activate or Deactivate the report policy.
                If no active then move to the status \'archive\'.
                Still can by found using filters button"""
    )

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
    )

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

    printer_id = fields.Many2one(
        'printnode.printer',
        string='Printer',
        required=True,
        ondelete='cascade',
    )

    printer_bin = fields.Many2one(
        'printnode.printer.bin',
        string='Printer Bin',
        required=False,
        domain='[("printer_id", "=", printer_id)]',
    )

    error = fields.Boolean(
        compute='_compute_print_rules',
    )

    notes = fields.Html(
        string='Note',
        compute='_compute_print_rules',
    )

    _sql_constraints = [
        ('rule_id', 'unique(user_id,report_id)', 'Rule should be unique.'),
    ]

    @api.depends('report_id', 'printer_id')
    def _compute_print_rules(self):

        def _html(message, icon='fa fa-question-circle-o'):
            return f'<span class="{icon}" title="{message}"></span>'

        def _ok(message):
            return False, _html(message, 'fa fa-circle-o')

        def _error(message):
            return True, _html(message, 'fa fa-exclamation-circle')

        for rule in self:

            if not rule.report_id or not rule.printer_id:
                rule.error, rule.notes = False, _html(_(
                    'Please, fill in the Report and Printer fields'
                ))
                continue

            error = rule.printer_id.printnode_check_report(rule.report_id, False)

            if error:
                rule.error, rule.notes = _error(error)
            else:
                rule.error, rule.notes = _ok(_('Configuration is valid.'))

    @api.onchange('printer_id')
    def _onchange_printer(self):
        """
        Reset printer_bin field to avoid bug with printing
        in wrong bin
        """
        self.printer_bin = self.printer_id.default_printer_bin.id
