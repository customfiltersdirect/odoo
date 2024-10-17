# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from odoo import fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'printnode.mixin', 'printnode.scenario.mixin']

    shipping_label_ids = fields.One2many(
        comodel_name='shipping.label',
        inverse_name='picking_id',
        string='Shipping Labels',
    )

    @staticmethod
    def _is_return_label_message(message, return_label_prefix):
        """
        Check if a message is a return label message.
        """
        for attach_id in message.attachment_ids:
            if attach_id.description and attach_id.description.find(return_label_prefix) != -1:
                return True
        return False

    @staticmethod
    def _get_return_label_attachments(message, return_label_prefix):
        """
        Check if the message is a return label message. If it is, create return label
        attachments for each attachment in that message and return them.
        """
        return_label_attachments = []

        if StockPicking._is_return_label_message(message, return_label_prefix):
            return_label_attachments = [
                (0, 0, {'document_id': attach.id, 'is_return_label': True})
                for attach in message.attachment_ids
            ]

        return return_label_attachments

    def _compute_state(self):
        """Override to catch status updates
        """
        previous_states = {rec.id: rec.state for rec in self}

        super()._compute_state()

        for record in self:
            # with_company() used to print on correct printer when calling from scheduled actions
            if record.id and previous_states.get(record.id) != record.state:
                record.with_company(record.company_id).print_scenarios(
                    'print_document_on_picking_status_change')

    def _put_in_pack(self, move_line_ids):
        package = super(StockPicking, self)._put_in_pack(move_line_ids)

        if package:
            self.print_scenarios(action='print_package_on_put_in_pack', packages_to_print=package)

        return package

    def button_validate(self):
        """ Overriding the default method to add custom logic with print scenarios
            for picking validate.
        """
        res = super(StockPicking, self).button_validate()

        if res is True:
            printed = self.print_scenarios(action='print_document_on_transfer')

            if printed:
                self.write({'printed': True})

            # Print product labels
            self.print_scenarios(action='print_product_labels_on_transfer')

            # Print lot labels
            self.print_scenarios(action='print_single_lot_labels_on_transfer_after_validation')
            self.print_scenarios(action='print_multiple_lot_labels_on_transfer_after_validation')

            # Print packages
            self.print_scenarios(action='print_packages_label_on_transfer')

            # Print operations
            self.print_scenarios(action='print_operations_document_on_transfer')

        return res

    def cancel_shipment(self):
        """
        Redefining a standard method
        """
        for stock_pick in self:
            shipping_label = stock_pick.shipping_label_ids.filtered(
                lambda sl: sl.tracking_numbers == self.carrier_tracking_ref
            )
            shipping_label.sudo().write({'label_status': 'inactive'})
        return super(StockPicking, self).cancel_shipment()

    def print_last_shipping_label(self):
        """ Print last shipping label if possible.
        """
        self.ensure_one()

        if self.picking_type_code != 'outgoing':
            return

        label = self.shipping_label_ids[:1]
        if not (label and label.label_ids and label.label_status == 'active'):
            if not self.env.company.print_sl_from_attachment:
                raise UserError(_(
                    'There are no available "shipping labels" for printing, '
                    'or last "shipping label" in state "In Active"'
                ))
            return self._print_sl_from_attachment(self.env.context.get('raise_exception_slp', True))
        return label.print_via_printnode()

    def send_to_shipper(self):
        """
        Redefining a standard method
        """
        user = self.env.user
        company = self.env.company

        auto_print = company.auto_send_slp and \
            company.printnode_enabled and user.printnode_enabled

        if auto_print and company.print_package_with_label:
            if self.picking_type_id == self.picking_type_id.warehouse_id.out_type_id:
                move_lines_without_package = self.move_line_ids_without_package.filtered(
                    lambda l: not l.result_package_id)
                if move_lines_without_package:
                    raise UserError(_('Some products on Delivery Order are not in Package. For '
                                      'printing Package Slips + Shipping Labels, please, put in '
                                      'pack remaining products. If you want to print only Shipping '
                                      'Label, please, deactivate "Print Package just after Shipping'
                                      ' Label" checkbox in PrintNode/Configuration/Settings'))

        if auto_print:
            # Simple check if shipping printer set, raise exception if no shipping printer found
            user.get_shipping_label_printer(self.carrier_id, raise_exc=True)

        super(StockPicking, self).send_to_shipper()

        if not self.carrier_tracking_ref:
            return

        self._create_shipping_labels()

        if auto_print and (self.shipping_label_ids or company.print_sl_from_attachment):
            self.with_context(raise_exception_slp=False).print_last_shipping_label()

    def _print_sl_from_attachment(self, raise_exception=True):
        self.ensure_one()

        domain = [
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
            ('company_id', '=', self.company_id.id),
        ]

        attachment = self.env['ir.attachment'].search(
            domain, order='create_date desc', limit=1
        )
        if not attachment:
            if raise_exception:
                raise UserError(_(
                    'There are no attachments in the current Transfer.'
                ))
            return

        domain.append(('create_date', '=', attachment.create_date))
        last_attachments = self.env['ir.attachment'].search(domain)

        printer = self.env.user.get_shipping_label_printer(self.carrier_id, raise_exc=True)

        for doc in last_attachments:
            params = {
                'title': doc.name,
                'type': 'qweb-pdf' if doc.mimetype == 'application/pdf' else 'qweb-text',
            }
            printer.printnode_print_b64(
                doc.datas.decode('ascii'), params, check_printer_format=False)

    def _create_backorder(self):
        backorders = super(StockPicking, self)._create_backorder()

        if backorders:
            printed = self.print_scenarios(
                action='print_document_on_backorder',
                ids_list=backorders.mapped('id'))

            if printed:
                backorders.write({'printed': True})

        return backorders

    def _get_label_attachments(self, message):
        label_attachments = []

        if len(self.package_ids) == len(message.attachment_ids):
            for index in range(len(self.package_ids)):
                vals = {
                    'document_id': message.attachment_ids[-index - 1].id,
                    'package_id': self.package_ids[index].id
                }
                label_attachments.append((0, 0, vals))
        else:
            for attach in message.attachment_ids:
                if (
                    self.carrier_id.delivery_type == 'sendcloud' and
                    'label' not in attach.name.lower()
                ):
                    continue
                else:
                    label_attachments.append((0, 0, {'document_id': attach.id}))

        return label_attachments

    def _create_shipping_labels(self):
        """
        Creates shipping labels for the current stock picking record.
        """
        messages_to_parse = self.env['mail.message'].search([
            ('model', '=', 'stock.picking'),
            ('res_id', '=', self.id),
            ('message_type', '=', 'notification'),
            ('body', 'ilike', self.carrier_tracking_ref),
        ], order='create_date asc')
        messages_to_parse = messages_to_parse.filtered('attachment_ids')

        # Get return shipping labels
        return_label_prefix = self.carrier_id.get_return_label_prefix()

        for i, message in enumerate(messages_to_parse):
            # Skip the message if it's a return label message
            if self._is_return_label_message(message, return_label_prefix):
                continue

            label_attachments = self._get_label_attachments(message)
            return_label_attachments = []

            next_message = messages_to_parse[i + 1] if i + 1 < len(messages_to_parse) else None
            if next_message:
                return_label_attachments = self._get_return_label_attachments(
                    next_message, return_label_prefix
                )

            shipping_label_vals = {
                'carrier_id': self.carrier_id.id,
                'picking_id': self.id,
                'tracking_numbers': self.carrier_tracking_ref,
                'label_ids': label_attachments,
                'return_label_ids': return_label_attachments,
                'label_status': 'active',
            }
            self.env['shipping.label'].create(shipping_label_vals)

    def _scenario_print_single_lot_labels_on_transfer_after_validation(
        self, scenario, number_of_copies=1, **kwargs
    ):
        """
        Print single lot label for each move line (after validation)
        Special method to provide custom logic of printing
        (like printing labels through wizards)
        """

        printed = self._scenario_print_single_lot_label_on_transfer(
            scenario=scenario,
            number_of_copies=number_of_copies,
            **kwargs
        )

        return printed

    def _scenario_print_multiple_lot_labels_on_transfer_after_validation(
        self, scenario, number_of_copies=1, **kwargs
    ):
        """
        Print multiple lot labels (depends on quantity) for each move line (after validation)
        Special method to provide custom logic of printing
        (like printing labels through wizards)
        """

        printed = self._scenario_print_multiple_lot_labels_on_transfer(
            scenario=scenario,
            number_of_copies=number_of_copies,
            **kwargs
        )

        return printed

    def _scenario_print_single_lot_label_on_transfer(
        self, scenario, report_id, printer_id, number_of_copies=1, **kwargs
    ):
        """
        Print single lot label for each move line (real time)
        Special method to provide custom logic of printing
        (like printing labels through wizards)
        """
        changed_move_lines = kwargs.get('changed_move_lines', self.move_line_ids)
        print_options = kwargs.get('options', {})

        return self._print_lot_labels_report(
            changed_move_lines,
            report_id,
            printer_id,
            with_qty=False,
            copies=number_of_copies,
            options=print_options)

    def _scenario_print_multiple_lot_labels_on_transfer(
        self, scenario, report_id, printer_id, number_of_copies=1, **kwargs
    ):
        """
        Print multiple lot labels (depends on quantity) for each move line (real time)
        Special method to provide custom logic of printing (like printing labels through wizards)
        """
        changed_move_lines = kwargs.get('changed_move_lines', self.move_line_ids)
        print_options = kwargs.get('options', {})

        return self._print_lot_labels_report(
            changed_move_lines,
            report_id,
            printer_id,
            with_qty=True,
            copies=number_of_copies,
            options=print_options)

    def _scenario_print_product_labels_on_transfer(
            self, scenario, number_of_copies=1, **kwargs
    ):
        """
        Print multiple product labels (depends on quantity) for each move line (after validation)
        Special method to provide custom logic of printing (like printing labels through wizards)
        """
        printed = self._scenario_print_multiple_product_labels_on_transfer(
            scenario=scenario,
            number_of_copies=number_of_copies,
            **kwargs
        )

        return printed

    def _scenario_print_single_product_label_on_transfer(
        self, scenario, number_of_copies=1, **kwargs
    ):
        """
        Print single product label for each move line (real time)
        Special method to provide custom logic of printing (like printing labels through wizards)
        """
        prepared_data = self._prepare_data_for_scenarios_to_print_product_labels(
            scenario,
            move_lines=kwargs.get('changed_move_lines', self.move_line_ids),
            **kwargs,
        )

        if not prepared_data:
            return False

        printed = prepared_data.get('printer_id').printnode_print(
            report_id=prepared_data.get('report_id'),
            objects=prepared_data.get('product_ids'),
            data=prepared_data.get('data'),
            copies=number_of_copies,
            options=prepared_data.get('print_options', {}),
        )

        return printed

    def _scenario_print_multiple_product_labels_on_transfer(
        self, scenario, number_of_copies=1, **kwargs
    ):
        """
        Print multiple product labels for each move line (real time)
        Special method to provide custom logic of printing (like printing labels through wizards)
        """
        prepared_data = self._prepare_data_for_scenarios_to_print_product_labels(
            scenario,
            move_lines=kwargs.get('changed_move_lines', self.move_line_ids),
            with_qty=True,
            **kwargs,
        )

        if not prepared_data:
            return False

        printed = prepared_data.get('printer_id').printnode_print(
            report_id=prepared_data.get('report_id'),
            objects=prepared_data.get('product_ids'),
            data=prepared_data.get('data'),
            copies=number_of_copies,
            options=prepared_data.get('print_options', {}),
        )

        return printed

    def _scenario_print_packages_label_on_transfer(
        self, report_id, printer_id, number_of_copies=1, **kwargs
    ):
        packages = self.mapped('package_ids')

        if packages:
            print_options = kwargs.get('options', {})
            return printer_id.printnode_print(
                report_id,
                packages,
                copies=number_of_copies,
                options=print_options,
            )

        return False

    def _scenario_print_document_on_picking_status_change(
        self, report_id, printer_id, number_of_copies=1, **kwargs
    ):
        print_options = kwargs.get('options', {})

        printed = printer_id.printnode_print(
            report_id,
            self,
            copies=number_of_copies,
            options=print_options,
        )
        return printed

    def _scenario_print_package_on_put_in_pack(
        self, report_id, printer_id, number_of_copies, packages_to_print, **kwargs
    ):
        """
        Print new packages from stock.picking.

        packages_to_print is a recordset of stock.quant.package to print
        """
        print_options = kwargs.get('options', {})

        printer_id.printnode_print(
            report_id,
            packages_to_print,
            copies=number_of_copies,
            options=print_options,
        )

    def _scenario_print_operations_document_on_transfer(
        self, report_id, printer_id, number_of_copies=1, **kwargs
    ):
        """
        Print reports from the invoice document on transfer scenario.
        """
        wizard = self.env['printnode.print.stock.move.reports.wizard'].with_context(
            active_id=self.id,
            active_model='stock.picking',
        ).create({
            'report_id': report_id.id,
            'printer_id': printer_id.id,
            'number_copy': number_of_copies,
        })
        wizard.do_print()

    def _change_number_of_lot_labels_to_one(self, custom_barcodes):
        """
        This method changes barcodes quantities to 1.
        Example of incoming data:
            defaultdict(<class 'list'>, {36: [('0002', 3), ('0003', 6)]})

        Return data example:
            defaultdict(<class 'list'>, {36: [('0002', 1), ('0003', 1)]})
        """
        new_custom_barcodes = defaultdict(list)
        for key, val in custom_barcodes.items():
            for code, qty in val:
                new_custom_barcodes[key].append((code, 1))

        return new_custom_barcodes

    def _get_product_lines_from_stock_move_lines(self, move_lines, **kwargs):
        """
        This method returns product_lines with product_id and quantity from stock_move_lines.
        """
        product_lines = []
        unit_uom = self.env.ref('uom.product_uom_unit')

        move_lines_qty_done = move_lines.filtered(lambda ml: ml.quantity > 0)
        for move_line in move_lines_qty_done:
            quantity_done = 1
            if move_line.product_uom_id == unit_uom:
                quantity_done = move_line.quantity

            product_lines.append((0, 0, {
                'product_id': move_line.product_id.id,
                'quantity': quantity_done,
            }))

        return product_lines

    def _print_lot_labels_report(
        self, changed_move_lines, report_id, printer_id,
        with_qty=False, copies=1, options=None
    ):
        """
        This method runs printing of lots labels. It can print single lot label for each lot or
        quantity based on quantity attribute
        """
        move_lines_with_lots_and_qty_done = changed_move_lines.filtered(
            lambda ml: ml.lot_id and not ml.printnode_printed and ml.quantity > 0)

        printed = False

        for move_line in move_lines_with_lots_and_qty_done:
            lots = self.env['stock.lot']

            if with_qty:
                for i in range(int(move_line.quantity)):
                    lots = lots.concat(move_line.lot_id)
            else:
                lots = lots.concat(move_line.lot_id)

            if lots:
                printer_id.printnode_print(
                    report_id,
                    lots,
                    copies=copies,
                    options=options,
                )

                move_line.write({'printnode_printed': True})
                printed = True

        return printed

    def _prepare_data_for_scenarios_to_print_product_labels(
        self, scenario, move_lines=None, with_qty=False, **kwargs,
    ):
        """
        This method prepares data to print product labels (using odoo Print Labels wizard)

        :param scenario: required current scenario
        :param moves: required stock moves from stock picking
        :param with_qty: optional boolean to change the move_quantity mode of wizard
        """
        product_lines = self._get_product_lines_from_stock_move_lines(move_lines=move_lines)

        move_lines_with_qty_done = move_lines.filtered(lambda ml: ml.quantity > 0)

        product_ids = move_lines_with_qty_done.mapped('product_id')

        if not product_ids:
            # Print nothing when no move lines where product with quantity_done > 0
            return False

        # In Odoo 16 there is a wizard to print labels, so we have to use it to avoid overriding
        # a lot of logic related to label format selection / printer selection / etc.
        wizard = self._init_product_label_layout_wizard(
            active_model='product.product',
            move_quantity='custom_per_product' if with_qty else 'custom',
            product_ids=product_ids,
            product_line_ids=product_lines,
            print_format=self.env.company.print_labels_format,
        )

        printing_data = self._prepare_printing_data(scenario, wizard, **kwargs)
        printing_data['product_ids'] = product_ids

        return printing_data

    def _init_product_label_layout_wizard(
        self, active_model, move_quantity, product_ids, product_line_ids, print_format, **kwargs
    ):
        """
        This method needed for ZPL Label Designer to allow pass additional fields to wizard.
        For now we use it to pass zld_label_id field to wizard.
        """
        try:
            return self.env['product.label.layout'].create({
                'active_model': active_model,
                'move_quantity': move_quantity,
                'product_ids': product_ids,
                'product_line_ids': product_line_ids,
                'print_format': print_format,
                **kwargs,  # Allow to pass any custom fields to wizard
            })
        except ValueError:
            raise UserError(
                _(
                    "One or more wrong fields for product.label.layout model passed: %s",
                    ', '.join(kwargs.keys())
                )
            )

    def _prepare_printing_data(self, scenario, wizard, **kwargs):
        """
        This method prepares all data required for scenarios to print something using Print Labels
        wizard (wizard parameter)
        """
        print_options = kwargs.get('options', {})

        # Printer from scenario should be used if it is set, otherwise use the default printer
        # from 'product.label.layout' wizard
        if scenario.printer_id:
            printer_id = scenario.printer_id
        else:
            # Manually call default method for printer_id to update printer based on
            # other wizard fields values
            printer_id, printer_bin = wizard._get_label_printer()
            # We also should replace printer bin to the value
            if printer_bin:
                print_options['bin'] = printer_bin.name

        # Get report
        xml_id, data = wizard._prepare_report_data()
        report_id = self.env.ref(xml_id)

        # Change type of dictionary keys to string
        if data['quantity_by_product']:
            data['quantity_by_product'] = self.change_dictionary_keys_type_to_string(
                data['quantity_by_product'])

        return {
            'printer_id': printer_id,
            'report_id': report_id,
            'data': data,
            'print_options': print_options,
        }

    def open_print_operation_reports_wizard(self):
        """ Returns action window with 'Print Operation Reports Wizard'
        """
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Print Operation Reports Wizard'),
            'res_model': 'printnode.print.stock.move.reports.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'printnode_base.printnode_print_stock_move_reports_wizard_form').id,
            'target': 'new',
            'context': self.env.context,
        }
