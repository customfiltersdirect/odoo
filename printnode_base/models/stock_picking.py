# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from odoo import models, fields, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'printnode.mixin', 'printnode.scenario.mixin']

    shipping_label_ids = fields.One2many(
        comodel_name='shipping.label',
        inverse_name='picking_id',
        string='Shipping Labels',
    )

    def _compute_field_value(self, field):
        """
        Override to catch status updates
        """
        super()._compute_field_value(field)

        # We cannot execute scenarios on new records (which have not yet been saved)
        saved_records = self.filtered(lambda record: record.id)

        if saved_records and field.name == 'state':
            # with_company() used to print on correct printer when calling from scheduled actions
            for record in saved_records:
                record.with_company(record.company_id).print_scenarios(
                    'print_document_on_picking_status_change')

    def _put_in_pack(self, move_line_ids, create_package_level=True):
        package = super(StockPicking, self)._put_in_pack(move_line_ids, create_package_level)

        if package:
            self.print_scenarios(action='print_package_on_put_in_pack', packages_to_print=package)

        return package

    def button_validate(self):
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

        return res

    def cancel_shipment(self):
        """
        Redefining a standard method
        """
        for stock_pick in self:
            shipping_label = stock_pick.shipping_label_ids.filtered(
                lambda sl: sl.tracking_numbers == self.carrier_tracking_ref
            )
            shipping_label.write({'label_status': 'inactive'})
        return super(StockPicking, self).cancel_shipment()

    def print_last_shipping_label(self):
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

        auto_print = user.company_id.auto_send_slp and \
            user.company_id.printnode_enabled and user.printnode_enabled

        if auto_print and user.company_id.print_package_with_label:
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

        tracking_ref = self.carrier_tracking_ref
        if not tracking_ref:
            return
        messages_to_parse = self.env['mail.message'].search([
            ('model', '=', 'stock.picking'),
            ('res_id', '=', self.id),
            ('message_type', '=', 'notification'),
            ('attachment_ids', '!=', False),
            ('body', 'ilike', tracking_ref),
        ])
        for message in messages_to_parse:
            self._create_shipping_label(message)

        if auto_print and (self.shipping_label_ids or user.company_id.print_sl_from_attachment):
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

    def _create_shipping_label(self, message):
        label_attachments = []
        if len(self.package_ids) == len(message.attachment_ids):
            for index in range(len(self.package_ids)):
                vals = {
                    'document_id': message.attachment_ids[-index - 1].id,
                    'package_id': self.package_ids[index].id
                }
                label_attachments.append((0, 0, vals))
        else:
            label_attachments = [
                (0, 0, {'document_id': attach.id}) for attach in message.attachment_ids
            ]

        # Get return shipping labels
        return_label_prefix = self.carrier_id.get_return_label_prefix()
        return_label_messages = self.env['mail.message'].search([
            ('model', '=', 'stock.picking'),
            ('res_id', '=', self.id),
            ('message_type', '=', 'notification'),
            ('attachment_ids.description', 'like', '%s%%' % return_label_prefix),
            ('create_date', '>=', message.create_date),
        ])

        return_label_attachments = []
        if return_label_messages:
            # All return labels are in the single message. There can be multiple message so we take
            # only the closest one (looks like this is impossible on practice but anyway)
            return_label_attachments = [
                (0, 0, {'document_id': attach.id, 'is_return_label': True})
                for attach in return_label_messages[0].attachment_ids
            ]

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
        new_move_lines = kwargs.get('new_move_lines', self.move_line_ids)
        print_options = kwargs.get('options', {})

        return self._print_lot_labels_report(
            new_move_lines,
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
        new_move_lines = kwargs.get('new_move_lines', self.move_line_ids)
        print_options = kwargs.get('options', {})

        return self._print_lot_labels_report(
            new_move_lines,
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
            move_lines=self.move_lines,
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
            move_lines=self.move_lines,
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
        print_options = kwargs.get('options', {})
        printer_id.printnode_print(
            report_id,
            packages,
            copies=number_of_copies,
            options=print_options,
        )

    def _scenario_print_document_on_picking_status_change(
        self, report_id, printer_id, number_of_copies=1, **kwargs
    ):
        print_options = kwargs.get('options', {})

        printer_id.printnode_print(
            report_id,
            self,
            copies=number_of_copies,
            options=print_options,
        )

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

    def _get_product_lines_from_stock_moves(self, move_lines, **kwargs):
        """
        This method returns product_lines with product_id and quantity from stock_move.
        """
        product_lines = []
        unit_uom = self.env.ref('uom.product_uom_unit')

        move_lines_with_qty_done = move_lines.filtered(lambda ml: ml.quantity_done > 0)

        for move_line in move_lines_with_qty_done:
            quantity_done = 1
            if move_line.product_uom == unit_uom:
                quantity_done = move_line.quantity_done

            product_lines.append((0, 0, {
                'product_id': move_line.product_id.id,
                'quantity': quantity_done,
            }))

        return product_lines

    def _get_product_lines_from_stock_move_lines(self, move_lines, **kwargs):
        """This method returns product_lines with product_id and quantity from stock_move_lines.
        """
        product_lines = []
        unit_uom = self.env.ref('uom.product_uom_unit')

        move_lines_with_lots_and_qty_done = move_lines.filtered(
            lambda ml: ml.qty_done > 0 and (ml.lot_id or ml.lot_name)
        )
        for move_line in move_lines_with_lots_and_qty_done:
            quantity_done = 1
            if move_line.product_uom_id == unit_uom:
                quantity_done = move_line.qty_done

            product_lines.append((0, 0, {
                'product_id': move_line.product_id.id,
                'quantity': quantity_done,
            }))

        return product_lines

    def _print_lot_labels_report(
        self, new_move_lines, report_id, printer_id,
        with_qty=False, copies=1, options=None
    ):
        """
        This method runs printing of lots labels. It can print single lot label for each lot or
        quantity based on qty_done attribute
        """
        move_lines_with_lots_and_qty_done = new_move_lines.filtered(
            lambda ml: ml.lot_id and not ml.printnode_printed and ml.qty_done > 0)

        printed = False

        for move_line in move_lines_with_lots_and_qty_done:
            lots = self.env['stock.production.lot']

            if with_qty:
                for i in range(int(move_line.qty_done)):
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
        :param move_lines: required stock moves from stock picking
        :param with_qty: optional boolean to change the picking_quantity mode of wizard
        """
        product_lines = self._get_product_lines_from_stock_moves(move_lines=move_lines)

        move_lines_with_qty_done = move_lines.filtered(lambda ml: ml.quantity_done > 0)

        product_ids = move_lines_with_qty_done.mapped('product_id')

        if not product_ids:
            # Print nothing when no move lines where product with quantity_done > 0
            return False

        # In Odoo 15 there is a wizard to print labels, so we have to use it to avoid overriding
        # a lot of logic related to label format selection / printer selection / etc.
        wizard = self.env['product.label.layout'].create({
            'active_model': 'product.product',
            'picking_quantity': 'custom_per_product' if with_qty else 'custom',
            'product_ids': product_ids,
            'product_line_ids': product_lines,
            'print_format': self.env.company.print_labels_format,
        })

        printing_data = self._prepare_printing_data(scenario, wizard, **kwargs)
        printing_data['product_ids'] = product_ids

        return printing_data

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
            printer_id, printer_bin = wizard._get_default_printer()
            # We also should replace printer bin to the value
            if printer_bin:
                print_options['bin'] = printer_bin.name

        # Get report
        xml_id, data = wizard._prepare_report_data()
        report_id = self.env.ref(xml_id)

        return {
            'printer_id': printer_id,
            'report_id': report_id,
            'data': data,
            'print_options': print_options,
        }
