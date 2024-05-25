# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductLabelLayoutMixin(models.AbstractModel):
    _name = 'printnode.label.layout.mixin'
    _description = 'Printnode Label Layout Mixin'

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

    # FIXME: Do we need this? Printer can be offline but user still can print
    # Because of wrong state of printer in DB
    status = fields.Char(
        related='printer_id.status',
    )

    is_dpc_enabled = fields.Boolean(
        default=lambda self: self._default_is_dpc_enabled(),
    )

    def _default_printer_id(self):
        """
        Returns only default printer from _get_default_printer()
        """
        printer, _ = self._get_default_printer()
        return printer

    def _default_is_dpc_enabled(self):
        """
        Returns True only if DPC enabled on the company level
        """
        return self.env.company.printnode_enabled

    def _get_default_printer(self):
        """
        Returns default printer for the user if DPC module enabled, otherwise - returns False
        """
        if self._default_is_dpc_enabled():
            # Workstation printer
            workstation_printer_id = self.env.user._get_workstation_device('printer_id')

            # Priority:
            # 1. Default Workstation Printer (User preferences)
            # 2. Default printer for current user (User Preferences)
            # 3. Default printer for current company (Settings)

            printer = workstation_printer_id or self.env.user.printnode_printer \
                or self.env.company.printnode_printer
            printer_bin = printer.default_printer_bin

            return printer, printer_bin

        return False, False

    @api.onchange("print_format")
    def _onchange_print_format(self):
        """
        Update printer based on selected report
        """
        # TODO: Actually this won't work for now because we do not support User Rules here
        # To be done in the future through adding some new menu?
        self.printer_id = self._default_printer_id()
