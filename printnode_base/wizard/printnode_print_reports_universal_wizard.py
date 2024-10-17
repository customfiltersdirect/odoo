# Copyright 2024 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import api, exceptions, fields, models, _


REPORT_DOMAIN = [
    ('report_type', 'in', ['qweb-pdf', 'qweb-text', 'py3o']),
    ('report_name', 'not in', [
        'sale.report_saleorder_pro_forma',
        'product.report_pricelist',
        'product.report_producttemplatelabel',
        'product.report_producttemplatelabel_dymo',
        'stock.label_product_product_view',
    ]),
]


class PrintnodePrintReportsUniversalWizard(models.TransientModel):
    _name = 'printnode.print.reports.universal.wizard'
    _description = 'Print Reports Wizard'

    report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        domain='[("id", "in", available_report_ids)]',
    )

    # Technical field to filter available reports for report_id field
    available_report_ids = fields.Many2many(
        comodel_name='ir.actions.report',
        compute='_compute_available_report_ids',
    )

    number_copy = fields.Integer(
        default=1,
        string='Copies',
    )

    record_model = fields.Char(
        string='Model',
        readonly=True,
        compute='_compute_record_model',
    )

    record_ids = fields.Text(
        string='Record IDs',
        readonly=True,
        compute='_compute_record_ids',
    )

    record_names = fields.Text(
        string='Will be printed',
        readonly=True,
        compute='_compute_record_names',
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

    status = fields.Char(related='printer_id.status')

    def _default_printer_id(self):
        """
        Return default printer for wizard
        """
        # There can be default report from settings (this method called before the deafult value
        # to report_id will be applied)
        report_id = self.report_id

        printer_id, _ = self.env.user.get_report_printer(report_id.id)

        return printer_id

    @api.constrains('number_copy')
    def _check_quantity(self):
        for rec in self:
            if rec.number_copy < 1:
                raise exceptions.ValidationError(
                    _('Quantity can not be less than 1')
                )

    @api.onchange('printer_id')
    def _onchange_printer(self):
        """
        Reset printer_bin field to avoid bug with printing
        in wrong bin
        """
        self.printer_bin = self.printer_id.default_printer_bin.id

    @api.onchange('report_id')
    def _onchange_wizard_printer(self):
        self.printer_id = self._default_printer_id()

    @api.depends('record_ids')
    def _compute_record_model(self):
        active_model = self.env.context.get('active_model')

        for rec in self:
            rec.record_model = active_model

    @api.depends('record_ids', 'record_model')
    def _compute_record_names(self):
        for rec in self:
            if rec.record_model and rec.record_ids:
                records = self.env[rec.record_model].browse(map(int, rec.record_ids.split(',')))
                rec.record_names = ", ".join(records.mapped('display_name'))

    @api.depends('record_model')
    def _compute_record_ids(self):
        active_ids = self.env.context.get('active_ids')

        for rec in self:
            rec.record_ids = ", ".join(map(str, active_ids))

    @api.depends('record_model')
    def _compute_available_report_ids(self):
        for rec in self:
            if rec.record_model:
                rec.available_report_ids = self.env['ir.actions.report'].search(
                    [*REPORT_DOMAIN, ('model', '=', rec.record_model)]
                )
            else:
                rec.available_report_ids = self.env['ir.actions.report']

    def do_print(self):
        if not self.report_id or not self.record_ids or not self.record_model:
            raise exceptions.UserError(_('No documents to print!'))

        record_ids = list(map(int, self.record_ids.split(',')))
        record_ids = self.env[self.record_model].browse(record_ids)

        # If immediate printing via PrintNode is disabled for the current user,
        # or if no printer is defined for the wizard, the PDF will be downloaded
        if not self.env.user.printnode_enabled or not self.printer_id:
            return self.report_id.with_context(download_only=True).report_action(docids=record_ids)

        options = {}
        if self.printer_bin:
            options['bin'] = self.printer_bin.name

        self.printer_id.printnode_print(
            self.report_id,
            record_ids,
            copies=self.number_copy,
            options=options,
        )

        title = _('Report was sent to printer')
        message = _(
            'Document "%(report)s" was sent to printer %(printer)s',
            report=self.report_id.name,
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
