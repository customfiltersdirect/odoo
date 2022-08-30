# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields

SECURITY_GROUP = 'printnode_base.printnode_security_group_user'


class PrintNodeScenarioAction(models.Model):
    """ Action for scenarios
    """
    _name = 'printnode.scenario.action'
    _description = 'PrintNode Scenario Action'

    name = fields.Char(
        string='Name',
        size=64,
        required=True,
    )

    code = fields.Char(
        string='Code',
        size=64,
        required=True,
    )

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
    )

    reports_model_id = fields.Many2one(
        'ir.model',
        string='Model For Reports',
        required=True,
        ondelete='cascade',
    )
