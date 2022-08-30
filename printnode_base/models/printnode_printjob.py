# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.
from datetime import datetime, timedelta
from odoo import models, fields


class PrintNodePrintJob(models.Model):
    """ PrintNode Job entity
    """

    _name = 'printnode.printjob'
    _description = 'PrintNode Job'

    # Actually, it is enough to have only 20 symbols but to be sure...
    printnode_id = fields.Char('Direct Print ID', size=64)

    printer_id = fields.Many2one(
        'printnode.printer',
        string='Printer',
        ondelete='cascade',
    )

    description = fields.Char(
        string='Label',
        size=64
    )

    def clean_printjobs(self, older_than_days):
        """
        Remove printjobs older than `older_than` days ago
        """
        days_ago = datetime.now() - timedelta(days=older_than_days)

        printjobs = self.search([('create_date', '<', days_ago)])
        printjobs.unlink()
