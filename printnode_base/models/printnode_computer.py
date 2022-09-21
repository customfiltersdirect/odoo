# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class PrintNodeComputer(models.Model):
    """ PrintNode Computer entity
    """
    _name = 'printnode.computer'
    _description = 'PrintNode Computer'

    printnode_id = fields.Integer('Direct Print ID')

    active = fields.Boolean(
        'Active',
        default=True
    )

    name = fields.Char(
        string='Name',
        size=64,
        required=True
    )

    status = fields.Char(
        string='Status',
        size=64
    )

    printer_ids = fields.One2many(
        'printnode.printer', 'computer_id',
        string='Printers'
    )

    account_id = fields.Many2one(
        'printnode.account',
        string='Account',
        ondelete='cascade',
    )

    _sql_constraints = [
        (
            'printnode_id',
            'unique(printnode_id)',
            'Computer ID should be unique.'
        ),
    ]
