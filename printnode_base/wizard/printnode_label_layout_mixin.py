# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductLabelLayoutMixin(models.AbstractModel):
    _name = 'printnode.label.layout.mixin'
    _description = 'Printnode Label Layout Mixin'

    printer_id = fields.Many2one(
        comodel_name='printnode.printer',
        compute='_compute_printer_id',
        readonly=False,
        store=True,
    )

    printer_bin = fields.Many2one(
        'printnode.printer.bin',
        string='Printer Bin',
        required=False,
        domain='[("printer_id", "=", printer_id)]',
        compute='_compute_printer_bin_id',
        readonly=False,
        store=True,
    )

    is_dpc_enabled = fields.Boolean(
        default=lambda self: self._default_is_dpc_enabled(),
    )

    @api.depends('printer_id')
    def _compute_printer_bin_id(self):
        for rec in self:
            rec.printer_bin = rec.printer_id.default_printer_bin

    @api.depends('print_format')
    def _compute_printer_id(self):
        for rec in self:
            printer, _ = rec._get_label_printer()
            rec.printer_id = printer

    def _default_printer_id(self):
        """
        Returns only default printer from _get_label_printer()
        """
        printer, _ = self._get_label_printer()
        return printer

    def _default_is_dpc_enabled(self):
        """
        Returns True only if DPC enabled on the company level
        """
        return self.env.company.printnode_enabled

    def _get_label_printer(self):
        """
        Priority:
        1. Printer from User Rules (if exists)
        2. Printer from Report Policy (if exists)
        3. Printer from Workstation (if exists)
        4. Default printer for current user (User Preferences)
        5. Default printer for current company (Settings)
        """
        self.ensure_one()

        if self._default_is_dpc_enabled():
            xml_id, _ = self._prepare_report_data()

            if xml_id:
                report_id = self.env.ref(xml_id).id
                return self.env.user.get_report_printer(report_id)

        workstation_printer_id = self.env.user._get_workstation_device('printer_id')

        printer = workstation_printer_id \
            or self.env.user.printnode_printer \
            or self.env.company.printnode_printer

        printer_bin = printer.default_printer_bin

        return printer, printer_bin
