# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields

SECURITY_GROUP = 'printnode_base.printnode_security_group_user'


class PrintNodeMixin(models.AbstractModel):
    _name = 'printnode.mixin'
    _description = 'Abstract PrintNode mixin'

    printnode_printed = fields.Boolean(default=False, copy=False)
