# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo.tests import common, tagged


@tagged('post_install', '-at_install', 'pn_job')  # can be run by test-tag
class TestPrintNodePrintJob(common.TransactionCase):

    def test_clean_printjobs(self):
        """
        Check method to clean outdated printjobs (older that 15 days)
        """
        PrintNodePrintJob = self.env['printnode.printjob']

        PrintNodePrintJob.create({'printnode_id': 1})
        printjob_2 = PrintNodePrintJob.create({'printnode_id': 2})

        self._update_printjob_create_date(
            printjob_2.id,
            (datetime.now() - timedelta(days=16)).strftime('%Y-%m-%d %H:%M:%S')
        )

        PrintNodePrintJob.clean_printjobs(older_than_days=15)

        # The only first one should exist
        self.assertEqual(
            len(PrintNodePrintJob.search([])),
            1,
            "More printjobs that should be after cleaning"  # NOQA
        )

    def _update_printjob_create_date(self, id, date):
        """
        This method is a hack in order to be able to define/redefine the create_date of printjob
        """
        self.env.cr.execute(
            "UPDATE printnode_printjob SET create_date = '%s' WHERE id = %s" % (date, id)
        )
