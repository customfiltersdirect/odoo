# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _
from odoo.exceptions import UserError


class ShippingLabel(models.Model):
    """ Shipping Label entity from Delivery Carrier
    """
    _name = 'shipping.label'
    _description = 'Shipping Label'
    _rec_name = 'picking_id'
    _order = 'create_date desc'

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Delivery Carrier',
        required=True,
        readonly=True,
    )

    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Delivery Order',
        domain='[("picking_type_id.code", "=", "outgoing")]',
        required=True,
        readonly=True,
    )

    tracking_numbers = fields.Char(
        string='Tracking Number(s)',
        readonly=True,
    )

    label_ids = fields.One2many(
        comodel_name='shipping.label.document',
        inverse_name='shipping_id',
        string='Shipping Label(s)',
        domain=[('is_return_label', '=', False)],
        readonly=True,
        copy=False,
    )

    return_label_ids = fields.One2many(
        comodel_name='shipping.label.document',
        inverse_name='shipping_id',
        string='Return Shipping Label(s)',
        domain=[('is_return_label', '=', True)],
        readonly=True,
        copy=False,
    )

    label_status = fields.Selection(
        [
            ('active', 'Active'),
            ('inactive', 'In Active'),
        ],
        string='Status',
    )

    def _get_attachment_list(self):
        self.ensure_one()
        attachment_list = []
        paper_id = self.carrier_id.autoprint_paperformat_id

        def update_attachment_list(label):
            doc = label.document_id
            params = {
                'title': doc.name,
                'type': 'qweb-pdf' if doc.mimetype == 'application/pdf' else 'qweb-text',
                'size': paper_id,
            }
            if label.package_id:
                params['package_id'] = label.package_id
            attachment_list.append((doc.datas.decode('ascii'), params))

        # If there is a label in the context, then the print was called through the print button
        # of one specific label
        if self._context.get('label'):
            label = self._context.get('label')
            update_attachment_list(label)
            return attachment_list

        for label in self.label_ids + self.return_label_ids:
            update_attachment_list(label)

        return attachment_list

    def print_via_printnode(self):
        """ Print Shipping Labels via the printnode service
        """
        user = self.env.user

        for shipping_label in self:
            printer = user.get_shipping_label_printer(shipping_label.carrier_id, raise_exc=True)

            attachment_list = shipping_label._get_attachment_list()
            if not attachment_list:
                continue

            for ascii_data, params in attachment_list:
                printer.printnode_print_b64(ascii_data, params)
                if params.get('package_id') and self.env.company.print_package_with_label:
                    report_id = self.env.company.printnode_package_report
                    if not report_id:
                        raise UserError(_(
                            'There are no available package report for printing, please, '
                            'define "Package Report to Print" in Direct Print / Settings menu'
                        ))

                    printer.printnode_print(report_id, params.get('package_id'))
