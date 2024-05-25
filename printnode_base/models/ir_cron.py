# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models


class ir_cron(models.Model):
    """ Model describing cron jobs (also called actions or tasks).
    """

    _inherit = "ir.cron"

    def _callback(self, cron_name, server_action_id, job_id):
        """
        Overriding the default method for adding the key "printnode_from_cron"
        to the context when executing cron.
        """

        contextual_self = self.with_context(printnode_from_cron=True)
        super(ir_cron, contextual_self)._callback(cron_name, server_action_id, job_id)
