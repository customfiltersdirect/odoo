# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PrintNodeActionMethod(models.Model):
    """ Action Button method
    """
    _name = 'printnode.action.method'
    _description = 'PrintNode Action Method'

    name = fields.Char(
        string='Name',
        size=64,
        required=True,
    )

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
    )

    method = fields.Char(
        string='Method',
        size=64,
        required=True,
    )

    _sql_constraints = [
        (
            'unique_action_method',
            'UNIQUE(model_id, method)',
            'The same method already exists!',
        ),
    ]

    @api.constrains('method')
    def _check_skip_method(self):
        methods_list = self.env['ir.config_parameter'].sudo() \
            .get_param('printnode_base.skip_methods', '').split(',')
        for action_method in self:
            if action_method.method in methods_list:
                raise ValidationError(
                    _('The following methods are not supported: %s', methods_list)
                )
