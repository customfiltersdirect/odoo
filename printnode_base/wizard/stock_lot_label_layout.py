# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models


class ProductLabelLayout(models.TransientModel):
    _name = 'lot.label.layout'
    _inherit = ['lot.label.layout', 'printnode.label.layout.mixin']

    def process(self):
        self.ensure_one()

        # Download PDF if no printer selected
        if not self.printer_id:
            # Update context to download on client side instead of printing
            # Check action_service.js file for details
            return super(ProductLabelLayout, self.with_context(download_only=True)).process()

        return super(
            ProductLabelLayout,
            self.with_context(printer_id=self.printer_id.id, printer_bin=self.printer_bin.id)
        ).process()

    def _prepare_report_data(self):
        """
        There is no such method in the parent class. But we add it to make this class compatible
        with _get_label_printer method from 'printnode.label.layout.mixin' mixin.
        """
        # Code below is copied from the parent class (process method)
        xml_id = 'stock.action_report_lot_label'
        if self.print_format == 'zpl':
            xml_id = 'stock.label_lot_template'

        # Originally this method should return xml_id and data. But we don't need data in this case
        return xml_id, None
