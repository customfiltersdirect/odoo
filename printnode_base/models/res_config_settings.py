# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import api, exceptions, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    printnode_enabled = fields.Boolean(
        readonly=False,
        related='company_id.printnode_enabled',
    )

    printnode_printer = fields.Many2one(
        'printnode.printer',
        readonly=False,
        related='company_id.printnode_printer',
    )

    print_labels_format = fields.Selection(
        readonly=False,
        related='company_id.print_labels_format',
    )

    printnode_recheck = fields.Boolean(
        readonly=False,
        related='company_id.printnode_recheck',
    )

    company_label_printer = fields.Many2one(
        'printnode.printer',
        readonly=False,
        related='company_id.company_label_printer',
    )

    auto_send_slp = fields.Boolean(
        readonly=False,
        related='company_id.auto_send_slp',
    )

    print_sl_from_attachment = fields.Boolean(
        readonly=False,
        related='company_id.print_sl_from_attachment',
    )

    im_a_teapot = fields.Boolean(
        readonly=False,
        related='company_id.im_a_teapot',
    )

    print_package_with_label = fields.Boolean(
        readonly=False,
        related='company_id.print_package_with_label',
    )

    printnode_package_report = fields.Many2one(
        readonly=False,
        related='company_id.printnode_package_report',
    )

    scales_enabled = fields.Boolean(
        readonly=False,
        related='company_id.scales_enabled',
    )

    printnode_scales = fields.Many2one(
        'printnode.scales',
        readonly=False,
        related='company_id.printnode_scales',
    )

    scales_picking_domain = fields.Char(
        readonly=False,
        related='company_id.scales_picking_domain',
    )

    printnode_notification_email = fields.Char(
        readonly=False,
        related='company_id.printnode_notification_email',
    )

    printnode_notification_page_limit = fields.Integer(
        readonly=False,
        related='company_id.printnode_notification_page_limit',
    )

    printnode_fit_to_page = fields.Boolean(
        readonly=False,
        related='company_id.printnode_fit_to_page',
    )

    dpc_api_key = fields.Char(
        string='API Key',
        default='',
    )

    dpc_status = fields.Char(
        string='Direct Print Client API Key Status',
        readonly=True,
    )

    dpc_is_allowed_to_collect_data = fields.Boolean(
        string="Allow to collect stats",
        default=True,
    )

    @api.onchange('print_package_with_label', 'print_sl_from_attachment')
    def _onchange_print_package_with_label(self):
        if self.print_package_with_label:
            self.print_sl_from_attachment = False
        if self.print_sl_from_attachment:
            self.print_package_with_label = False

    @api.onchange('group_stock_tracking_lot')
    def _onchange_group_stock_tracking_lot(self):
        """
        Disable the "Print Package just after Shipping Label" setting
        if the user disables the "Packages" setting
        """
        if not self.group_stock_tracking_lot and self.print_package_with_label:
            self.print_package_with_label = False

            return {
                'warning': {
                    'title': _("Warning!"),
                    'message': _(
                        'Disabling this option will also automatically disable option '
                        '"Print Package just after Shipping Label" in Direct Print settings'
                    ),
                }
            }

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        accounts = self.env['printnode.account'].search([]).sorted(key=lambda r: r.id)

        if accounts:
            # First account is main account. All other accounts - not allowed anymore
            # (but will still work for better customer experience)
            account = accounts[0]

            res.update(
                dpc_api_key=account.api_key,
                dpc_status=account.status,
                dpc_is_allowed_to_collect_data=account.is_allowed_to_collect_data,
            )

        return res

    def set_values(self):
        if self.print_package_with_label and not self.group_stock_tracking_lot:
            self.group_stock_tracking_lot = True

        if self.dpc_api_key:
            self.env['printnode.account'].update_main_account(
                self.dpc_api_key,
                self.dpc_is_allowed_to_collect_data)

        super(ResConfigSettings, self).set_values()

    def activate_account(self):
        """
        Callback for activate button. Finds and activates the main account
        """
        accounts = self.env['printnode.account'].search([]).sorted(key=lambda r: r.id)

        if accounts:
            return accounts[0].activate_account()
        else:
            raise exceptions.UserError(_('Please, add an account before activation'))

    def import_devices(self):
        accounts = self.env['printnode.account'].search([]).sorted(key=lambda r: r.id)

        if accounts:
            return accounts[0].import_devices()
        else:
            raise exceptions.UserError(_('Please, add an account before importing printers'))
