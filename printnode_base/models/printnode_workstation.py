# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class PrintnodeWorkstation(models.Model):
    _name = 'printnode.workstation'
    _description = 'Printnode Workstation'

    name = fields.Char(
        string='Workstation Name',
        required=True,
    )

    printer_id = fields.Many2one(
        'printnode.printer',
        string='Default Workstation Printer',
    )

    label_printer_id = fields.Many2one(
        'printnode.printer',
        string='Default Workstation Shipping Label Printer',
    )

    scales_id = fields.Many2one(
        'printnode.scales',
        string='Default Workstation Scales',
    )

    _sql_constraints = [
        ('name', 'unique(name)', 'Workstation name must be unique'),
    ]

    @api.model
    def get_workstation_devices(self):
        """
        This method used for status menu.

        Return information about workstation devices in format:
        [printer, label_printer, scales]
        """
        workstation = self.get_workstation()

        devices = []

        for field in ('printer_id', 'label_printer_id', 'scales_id'):
            devices.append({
                'label': getattr(PrintnodeWorkstation, field).string,
                'id': None,
                'name': None,
            })

            device = getattr(workstation, field, None)

            if device:
                devices[-1].update(
                    id=device.id,
                    name=device.name,
                )

        return devices

    @api.model
    def get_workstation(self):
        id = self.env.context.get('printnode_workstation_id')

        if id:
            # We have to use exists() to make sure the entry exists in the database and
            # not just in the ORM cache.
            workstation = self.env['printnode.workstation'].browse(id).exists()
            return workstation

        return None
