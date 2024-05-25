# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, _


class Base(models.AbstractModel):
    _inherit = 'base'

    def run_printnode_universal_wizard(self):
        """ Returns action window with 'Print Attachments Wizard'
        """
        return {
            'type': 'ir.actions.act_window',
            'name': _('Print Attachments Wizard'),
            'res_model': 'printnode.attach.universal.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('printnode_base.printnode_attach_universal_wizard_form').id,
            'target': 'new',
            'context': self.env.context,
        }

    def run_printnode_print_reports_universal_wizard(self):
        """ Returns action window with 'Print Reports Wizard'
        """
        return {
            'type': 'ir.actions.act_window',
            'name': _('Print Reports Wizard'),
            'res_model': 'printnode.print.reports.universal.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'printnode_base.printnode_print_reports_universal_wizard_form').id,
            'target': 'new',
            'context': self.env.context,
        }
