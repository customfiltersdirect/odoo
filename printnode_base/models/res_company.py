# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


REPORT_DOMAIN = [
    '|', ('model', '=', 'product.product'), ('model', '=', 'product.template'),
    ('report_type', 'in', ['qweb-pdf', 'qweb-text', 'py3o']),
    ('report_name', '!=', 'product.report_pricelist'),
]


class Company(models.Model):
    _inherit = 'res.company'

    printnode_enabled = fields.Boolean(
        string='Enable Direct Printing',
        default=False,
    )

    printnode_printer = fields.Many2one(
        'printnode.printer',
        string='Printer',
    )

    print_labels_format = fields.Selection(
        [
            ('dymo', 'Dymo'),
            ('2x7xprice', '2 x 7 with price'),
            ('4x7xprice', '4 x 7 with price'),
            ('4x12', '4 x 12'),
            ('4x12xprice', '4 x 12 with price'),
            ('zpl', 'ZPL Labels'),
            ('zplxprice', 'ZPL Labels with price')
        ],
        string="Default Product Labels Format",
        help='Set default label printing format')

    printnode_recheck = fields.Boolean(
        string='Mandatory check Printing Status',
        default=False,
    )

    company_label_printer = fields.Many2one(
        'printnode.printer',
        string='Shipping Label Printer',
    )

    auto_send_slp = fields.Boolean(
        string='Auto-send to Shipping Label Printer',
        default=False,
    )

    print_sl_from_attachment = fields.Boolean(
        string='Use Attachments Printing for Shipping Label(s)',
        default=False,
    )

    im_a_teapot = fields.Boolean(
        string='Show success notifications',
        default=True,
    )

    print_package_with_label = fields.Boolean(
        string='Print Package just after Shipping Label',
        default=False,
    )

    printnode_package_report = fields.Many2one(
        'ir.actions.report',
        string='Package Report to Print',
    )

    scales_enabled = fields.Boolean(
        string='Enable Scales Integration',
        default=False,
    )

    printnode_scales = fields.Many2one(
        'printnode.scales',
        string='Default Scales',
    )

    scales_picking_domain = fields.Char(
        string='Picking criteria for auto-weighing',
        default='[["picking_type_code","=","outgoing"]]'
    )

    printnode_notification_email = fields.Char(
        string="Direct Print Notification Email",
    )

    printnode_notification_page_limit = fields.Integer(
        string="Direct Print Notification Page Limit",
        default=100,
    )

    printnode_fit_to_page = fields.Boolean(
        string='Disable fit to the page size',
        default=False,
    )

    debug_logging = fields.Boolean(
        string='Debug logging',
        default=False,
        help='By enabling this feature, all requests will be logged. '
             'You can find them in "Settings - Technical - Logging" menu.',
    )

    log_type_ids = fields.Many2many(
        comodel_name='printnode.log.type',
        string='Logs to write',
        required=False,
    )

    printing_scenarios_from_crons = fields.Boolean(
        string='Allow to execute printing scenarios from crons',
        default=True,
    )

    secure_printing = fields.Boolean(
        string='Printing without sending documents to the print server',
        default=False,
    )
