# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ShippingLabelDocument(models.Model):
    """ Attached Document to the Shipping Label entity
    """
    _name = 'shipping.label.document'
    _description = 'Shipping Label Document'
    _rec_name = 'document_id'

    shipping_id = fields.Many2one(
        string='Related Shipping Label',
        comodel_name='shipping.label',
        ondelete='cascade',
    )

    document_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Shipping Label Document',
    )

    package_id = fields.Many2one(
        string='Package',
        comodel_name='stock.quant.package',
        ondelete='set null',
    )

    is_return_label = fields.Boolean(
        string='Is Return Shipping label?',
        default=False,
    )

    def print_label_with_package_via_printnode(self):
        """ Print Shipping Labels with package via the printnode service
        """
        self.shipping_id.with_context(label=self).print_via_printnode()
