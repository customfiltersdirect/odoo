# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'printnode.mixin', 'printnode.scenario.mixin']

    def action_post(self):
        """ Overriding the default method to add custom logic with print scenarios for account moves
        """
        res = super(AccountMove, self).action_post()

        # action_post method do not return anything. So in case no error was raised,
        # Just go ahead and execute print scenario if it is found and if move_type is
        # Customer Invoice / Customer Credit Note / Vendor Bill / Vendor Credit Note
        for move in self:
            if move.move_type in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund'] and \
                    move.state == 'posted':
                move.print_scenarios(action='print_invoice_document_after_validation')

        return res
