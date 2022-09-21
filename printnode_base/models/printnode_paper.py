# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class PrintNodePaper(models.Model):
    """ PrintNode Paper entity
    """
    _name = 'printnode.paper'
    _description = 'PrintNode Paper'

    name = fields.Char(
        'Name',
        size=64,
        required=True
    )

    width = fields.Integer('Width')

    height = fields.Integer('Height')
