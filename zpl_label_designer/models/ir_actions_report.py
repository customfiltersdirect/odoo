from odoo import api, models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _render_qweb_text(self, report_ref, docids, data=None):
        """
        :rtype: bytes
        """
        if data and data.get('is_zld_product_label', False):
            docids = self._get_docids_for_zld_product_label(data)

        return super()._render_qweb_text(report_ref, docids, data)

    def _get_docids_for_zld_product_label(self, data):
        """
        This method add records to use in the report based on the active_model and quantity from
        the wizard.
        """
        docids = []
        for p, q in data.get('quantity_by_product').items():
            docids += [int(p) for i in range(q)]

        return docids
