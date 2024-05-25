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
