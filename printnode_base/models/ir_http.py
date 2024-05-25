# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        # Since Odoo 14, session_info() returns User->Default Company, not General Company.
        # This influence the "Print" and "Downloads" interface menus. If the module's Printnode
        # settings are different between General Company and User->Default Company, then the display
        # of the "Print" and "Downloads" menus may not be correct.
        res = super(IrHttp, self).session_info()

        dpc_company_enabled = False
        dpc_user_enabled = False

        if self.env.user.has_group("printnode_base.printnode_security_group_user") \
                and self.env.company.printnode_enabled:
            dpc_company_enabled = True

            if self.env.user.printnode_enabled:
                dpc_user_enabled = True

        res.update({
            'dpc_company_enabled': dpc_company_enabled,
            'dpc_user_enabled': dpc_user_enabled,
        })

        return res
