# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _
from odoo.exceptions import UserError


class User(models.Model):
    """ User entity. Add 'Default Printer' field (no restrictions).
    """
    _inherit = 'res.users'

    printnode_enabled = fields.Boolean(
        string='Auto-print via Direct Print',
        default=False,
    )

    printnode_printer = fields.Many2one(
        'printnode.printer',
        string='Default Printer',
    )

    scales_enabled = fields.Boolean(
        string='Auto-measure with Scales',
        default=False,
    )

    printnode_scales = fields.Many2one(
        'printnode.scales',
        string='Default Scales',
    )

    user_label_printer = fields.Many2one(
        'printnode.printer',
        string='Shipping Label Printer',
    )

    printnode_rule_ids = fields.One2many(
        comodel_name='printnode.rule',
        inverse_name='user_id',
        string='Direct Print Rules',
    )

    @property
    def SELF_READABLE_FIELDS(self):
        readable_fields = [
            'printnode_enabled',
            'printnode_printer',
            'printnode_scales',
            'scales_enabled',
            'user_label_printer',
            'printnode_rule_ids',
        ]

        return super().SELF_READABLE_FIELDS + readable_fields

    @property
    def SELF_WRITEABLE_FIELDS(self):
        writable_fields = [
            'printnode_enabled',
            'printnode_printer',
            'printnode_scales',
            'scales_enabled',
            'user_label_printer',
        ]

        return super().SELF_WRITEABLE_FIELDS + writable_fields

    def get_shipping_label_printer(self, carrier_id=None, raise_exc=False):
        """
        Printer search sequence:
        1. Default Workstation Shipping Label Printer (Settings)
        2. Default Delivery Carrier Printer
        3. Default Shipping Label Printer for current user (User Preferences)
        4. Default Shipping Label Printer for current company (Settings)
        """
        company = self.env.company

        # There can be printer for the current workstation
        workstation_label_printer_id = self._get_workstation_device('label_printer_id')

        if workstation_label_printer_id:
            return workstation_label_printer_id

        delivery_carrier_printer = carrier_id.printer_id if carrier_id else None

        printer = (delivery_carrier_printer or self.user_label_printer
                   or company.company_label_printer)

        if not printer and raise_exc:
            raise UserError(_(
                'Neither on company level, no on user level default label printer '
                'is defined. Please, define it.'
            ))

        return printer

    def get_report_printer(self, report_id):
        """
        :param int report_id: ID of the report to searching

        Printer search sequence:
        1. Printer from Print Action Button or Print Scenario (if specified, out of this method)

        2. Printer from User Rules (if exists)
        3. Printer from Report Policy (if exists)
        4. Default Workstation Printer (Settings)
        5. Default printer for current user (User Preferences)
        6. Default printer for current company (Settings)
        """
        self.ensure_one()

        rule = self.printnode_rule_ids.filtered(lambda r: r.report_id.id == report_id)[:1]

        if rule.printer_id:
            return rule.printer_id, rule.printer_bin

        report_policy = self.env['printnode.report.policy'].search(
            [('report_id', '=', report_id)], limit=1)

        if report_policy.printer_id:
            return report_policy.printer_id, report_policy.printer_bin

        # There can be printer for the current workstation
        workstation_printer_id = self._get_workstation_device('printer_id')

        printer = (workstation_printer_id or self.printnode_printer
                   or self.env.company.printnode_printer)

        printer_bin = printer.default_printer_bin

        return printer, printer_bin

    def get_scales(self):
        """
        Scales search sequence:
        3. Default Workstation Scales (Settings)
        4. Default scales for current user (User Preferences)
        5. Default scales for current company (Settings)
        """
        self.ensure_one()

        # There can be scales for the current workstation
        workstation_scales_id = self._get_workstation_device('scales_id')

        scales = workstation_scales_id or self.printnode_scales or self.env.company.printnode_scales

        return scales

    def _get_workstation_device(self, device):
        """
        Helper method to get correct device for the current workstation
        """
        workstation = self.env['printnode.workstation'].get_workstation()

        if not workstation:
            return None

        return getattr(workstation, device, None)
