# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PrintNodePrinter(models.Model):
    """ PrintNode Scales entity
    """
    _name = 'printnode.scales'
    _description = 'PrintNode Scales'

    printnode_id = fields.Integer('Printnode ID')

    active = fields.Boolean(
        'Active',
        default=True,
    )

    online = fields.Boolean(
        string='Online',
        compute='_compute_scales_status',
        store=True,
        readonly=True,
    )

    name = fields.Char(
        'Device Name',
        size=64,
        required=True,
    )

    device_num = fields.Integer(
        'Device Num',
        required=True,
    )

    status = fields.Char(
        'PrintNode Status',
        size=64,
    )

    computer_id = fields.Many2one(
        'printnode.computer',
        string='Computer',
        ondelete='cascade',
        required=True,
    )

    account_id = fields.Many2one(
        'printnode.account',
        string='Account',
        readonly=True,
        related='computer_id.account_id',
    )

    _sql_constraints = [
        (
            'printnode_id',
            'unique(computer_id, printnode_id)',
            'Scales ID should be unique.'
        ),
    ]

    @api.depends('name', 'device_num', 'computer_id.name')
    def _compute_display_name(self):
        for scales in self:
            scales.display_name = f'{scales.name}-{scales.device_num} ({scales.computer_id.name})'

    @api.depends('status', 'computer_id.status')
    def _compute_scales_status(self):
        """
        Check computer and printer status
        """
        for rec in self:
            rec.online = rec.status in ['online'] and rec.computer_id.status in ['connected']

    def get_scales_measure_kg(self, show_error_on_zero=True):
        """ Gets scales measure (kg) using PrintNode service.
            Returns mass in kg.
        """
        scales_results = '/computer/{}/scale/{}/{}'.format(
            self.computer_id.printnode_id,
            self.name,
            self.device_num,
        )
        result = self.account_id._send_printnode_request(scales_results)

        if not result:
            raise UserError(
                _('Scales are not online. Please, check that they are available (%s).')
                % self.name
            )

        mass_micrograms = result.get('mass')[0]

        if show_error_on_zero and mass_micrograms == 0.0:
            raise UserError(
                _('Scales "(%s)" showing ZERO weight. Check that you\'ve placed package properly.')
                % self.name
            )

        if not mass_micrograms or mass_micrograms < 0.0:
            raise UserError(
                _('Scales "(%s)" showing negative weight. Please, calibrate them.')
                % self.name
            )

        mass_kg = mass_micrograms / 1000000000
        return mass_kg
