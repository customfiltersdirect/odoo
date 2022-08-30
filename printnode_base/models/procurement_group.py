from odoo import api, models


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def run_scheduler(self, use_new_cursor=False, company_id=False):
        # Update context because we want to execute some print scenarios from this cron
        return super(
            ProcurementGroup,
            self.with_context(from_cron=True)
        ).run_scheduler(use_new_cursor, company_id)
