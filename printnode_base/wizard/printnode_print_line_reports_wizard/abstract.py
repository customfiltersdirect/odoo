# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import api, exceptions, fields, models, _


class PrintnodePrintAbstractLineReportsWizard(models.AbstractModel):
    _name = 'printnode.abstract.print.line.reports.wizard'
    _description = 'Abstract wizard model for printing reports for lines'

    number_copy = fields.Integer(
        default=1,
        string='Copies',
    )

    report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        domain=lambda self: self._get_report_domain(),
    )

    # This field should be overridden in child models
    record_line_ids = fields.One2many(
        comodel_name='printnode.abstract.print.line.reports.wizard.line',
        inverse_name='wizard_id',
        string='Records',
        default=lambda self: self._default_record_line_ids(),
    )

    printer_id = fields.Many2one(
        comodel_name='printnode.printer',
        default=lambda self: self._default_printer_id(),
    )

    printer_bin = fields.Many2one(
        'printnode.printer.bin',
        string='Printer Bin',
        required=False,
        domain='[("printer_id", "=", printer_id)]',
    )

    status = fields.Char(
        related='printer_id.status',
    )

    def _get_report_domain(self):
        return []

    def _default_printer_id(self):
        """
        Return default printer for wizard

        Priority:
        1. Printer from User Rules (if exists)
        2. Print from Report Policy (if exists)
        3. Default Workstation Printer (User preferences)
        4. Default printer for current user (User Preferences)
        5. Default printer for current company (Settings)
        """
        report_id = self.report_id

        if not report_id:
            return None

        return self.env.user.get_report_printer(report_id.id)[0]

    @api.constrains('number_copy')
    def _check_number_copy(self):
        for rec in self:
            if rec.number_copy < 1:
                raise exceptions.ValidationError(_('Quantity can not be less than 1'))

    @api.onchange('report_id')
    def _change_wizard_printer(self):
        self.printer_id = self._default_printer_id()

    def get_report(self):
        self.ensure_one()
        return self.report_id

    def get_docids(self):
        self.ensure_one()

        objects = self.record_line_ids.mapped('record_id')
        return objects

    def _default_record_line_ids(self):
        raise NotImplementedError()

    def _get_line_model(self):
        raise NotImplementedError()

    def do_print(self):
        self.ensure_one()

        if not self.record_line_ids:
            raise exceptions.UserError(_('No documents to print!'))

        report = self.get_report()

        # Create empty recordset
        docids = self._get_line_model().browse()

        # Add copies
        for line_id in self.record_line_ids:
            for i in range(line_id.quantity):
                docids += line_id.record_id

        if not docids:
            raise exceptions.UserError(_('No documents to print!'))

        # If no printer than download PDF
        if not self.printer_id:
            return report.with_context(download_only=True).report_action(docids=docids)

        options = {}
        if self.printer_bin:
            options['bin'] = self.printer_bin.name

        # If printer than send to printnode
        self.printer_id.printnode_print(
            report,
            docids,
            options=options,
            copies=self.number_copy,
        )

        title = _('Report was sent to printer')
        message = _(
            'Document "%(report)s" was sent to printer %(printer)s',
            report=report.name,
            printer=self.printer_id.name,
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': 'success',
                'sticky': False,
            },
        }


class PrintnodePrintAbstractLineReportsWizardLine(models.TransientModel):
    _name = 'printnode.abstract.print.line.reports.wizard.line'
    _description = 'Record Line'

    # This field should be overridden in child models
    record_id = fields.Integer(
        required=True,
    )

    # This field should be populated in child models
    name = fields.Char(string='Name')

    quantity = fields.Integer(
        required=True,
        default=1,
    )

    # This field should be overridden in child models
    wizard_id = fields.Many2one(
        comodel_name='printnode.abstract.print.line.reports.wizard',
    )

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity < 0:
                raise exceptions.ValidationError(
                    _(
                        'Quantity can not be less than 0 for {product}'
                    ).format(**{
                        'product': rec.name,
                    })
                )
