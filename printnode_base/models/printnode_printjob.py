# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.
from datetime import datetime, timedelta
from odoo import api, models, fields

from .constants import Constants


class PrintNodePrintJob(models.Model):
    """ PrintNode Job entity
    """

    _name = 'printnode.printjob'
    _inherit = 'printnode.logger.mixin'
    _description = 'PrintNode Job'

    # Actually, it is enough to have only 20 symbols but to be sure...
    printnode_id = fields.Char(
        string='Direct Print ID',
        size=64,
        default='__New_ID__',
    )

    printer_id = fields.Many2one(
        'printnode.printer',
        string='Printer',
        ondelete='cascade',
    )

    description = fields.Char(
        string='Label',
        size=64
    )

    attachment_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attachments',
        ondelete='cascade',
    )

    def unlink(self):
        self.attachment_id.unlink()
        return super().unlink()

    @api.model
    def create_job(self, title='', printer_id=False, content=None, content_type=None):
        create_vals = {
            'printer_id': printer_id,
            'description': title,
        }
        res = super().create(create_vals)

        if self.env.company.secure_printing and content:
            attachment_id = self._create_attachment(
                name=title or f'{res._name.replace(".", "_")}_{res.id}',
                res_model=self._name,
                res_id=res.id,
                content=content,
                content_type=content_type,
            )

            res['attachment_id'] = attachment_id.id

            self.printnode_logger(
                Constants.REQUESTS_LOG_TYPE,
                f'Attachment (id:{attachment_id.id}) created to printjob (id:{res.id}) in "secure printing" mode.',  # NOQA
            )

        return res

    def _create_attachment(self, name, res_model, res_id, content, content_type):
        attachment_value = {
            'name': name,
            'res_model': res_model,
            'res_id': res_id,
            'datas': content if isinstance(content, bytes) else content.encode(),
        }

        if content_type == 'raw_base64':
            attachment_value['mimetype'] = 'text/plain'

        attachment_id = self.env['ir.attachment'].sudo().create(attachment_value)

        return attachment_id

    def clean_printjobs(self, older_than_days):
        """
        Remove printjobs older than `older_than` days ago
        """
        days_ago = datetime.now() - timedelta(days=older_than_days)

        printjobs = self.search([('create_date', '<', days_ago)])

        printjobs.attachment_id.unlink()
        printjobs.unlink()
