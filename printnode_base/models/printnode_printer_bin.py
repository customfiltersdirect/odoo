# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class PrinterBin(models.Model):
    """ PrintNode Printer Bin
    """
    _name = 'printnode.printer.bin'
    _description = 'PrintNode Printer Bin'

    name = fields.Char(
        'Bin Name',
        required=True,
    )

    printer_id = fields.Many2one(
        'printnode.printer',
        string='Printer',
        required=True,
        ondelete='cascade',
    )
