# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import api, exceptions, fields, models, _


class PrintnodeAttachUniversalWizard(models.TransientModel):
    _name = 'printnode.attach.universal.wizard'
    _description = 'Print Attachments via Direct Print'

    attach_line_ids = fields.One2many(
        comodel_name='printnode.attach.line',
        inverse_name='wizard_id',
        string='Attachments',
    )

    with_custom_qty = fields.Boolean(
        string="Custom quantity for each attachment",
        default=False,
    )

    number_copy = fields.Integer(
        default=1,
        string='Copies',
    )

    printer_id = fields.Many2one(
        comodel_name='printnode.printer',
        default=lambda self: self._default_printer_id(),
        required=True,
    )

    printer_bin = fields.Many2one(
        'printnode.printer.bin',
        string='Printer Bin',
        required=False,
        domain='[("printer_id", "=", printer_id)]',
    )

    def _default_printer_id(self):
        """
        Returns default printer to print attachments
        """
        # Workstation printer
        workstation_printer_id = self.env.user._get_workstation_device('printer_id')

        # Priority:
        # 1. Default Workstation Printer (User preferences)
        # 2. Default printer for current user (User Preferences)
        # 3. Default printer for current company (Settings)
        return workstation_printer_id or self.env.user.printnode_printer or \
            self.env.company.printnode_printer

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

    def do_print(self):
        printer = self.printer_id

        if not self.attach_line_ids:
            raise exceptions.UserError(_('No attachments to print!'))

        for line in self.attach_line_ids:
            # Allow to print multiple copies (including custom quantity for each attachment)
            copies = self.number_copy
            if self.with_custom_qty:
                copies = line.quantity

            params = {
                'title': line.name,
                'type': 'qweb-pdf' if line.mimetype == 'application/pdf' else 'qweb-text',
                'options': {'bin': self.printer_bin.name} if self.printer_bin else {},
                'copies': copies,
            }
            printer.printnode_print_b64(
                line.bin_data.decode('ascii'), params, check_printer_format=False)

        attachment_names = [al.attachment_id.name for al in self.attach_line_ids]
        title = _('Documents were sent to printer')
        message = _(
            'Documents "%(attachment)s" were sent to printer %(printer)s',
            attachment=', '.join(attachment_names),
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

    @api.model
    def default_get(self, fields_list):
        res = super(PrintnodeAttachUniversalWizard, self).default_get(fields_list)

        res_ids = self.env.context.get('active_ids')
        res_model = self.env.context.get('active_model')
        if not (res_ids and res_model):
            return res

        attachments = self.env['ir.attachment'].search([
            ('res_id', 'in', res_ids),
            ('res_model', '=', res_model),
            ('company_id', '=', self.env.company.id),
        ], order='create_date desc')
        lines_vals = [{'attachment_id': rec.id} for rec in attachments]
        attach_lines = self.env['printnode.attach.line'].create(lines_vals)
        res['attach_line_ids'] = [(6, 0, attach_lines.ids)]
        return res

    @api.onchange('with_custom_qty')
    def _onchange_with_custom_qty(self):
        """
        Set quantity field for attachment lines to one if with_custom_qty field is false
        """
        for line in self.attach_line_ids:
            line.quantity = 1


class PrintnodeAttachLine(models.TransientModel):
    _name = 'printnode.attach.line'
    _description = 'Printnode Attachment Line'

    attachment_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attachment',
    )
    name = fields.Char(
        related='attachment_id.name',
        string='Name',
    )
    bin_data = fields.Binary(
        related='attachment_id.datas',
        string='Size',
    )
    mimetype = fields.Char(
        related='attachment_id.mimetype',
        string='Type',
    )
    date = fields.Datetime(
        related='attachment_id.create_date',
        string='Creation Date',
    )
    quantity = fields.Integer(
        required=True,
        default=1,
    )
    with_custom_qty = fields.Boolean(
        related='wizard_id.with_custom_qty',
        string='With Custom Quantity',
    )
    wizard_id = fields.Many2one(
        comodel_name='printnode.attach.universal.wizard',
        string='Parent Wizard',
    )

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity < 1:
                raise exceptions.ValidationError(
                    _(
                        'Quantity can not be less than 1 for product {product}'
                    ).format(**{
                        'product': rec.product_id.display_name,
                    })
                )
