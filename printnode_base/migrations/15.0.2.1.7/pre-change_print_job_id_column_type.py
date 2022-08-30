# Copyright 2022 VentorTech OU
# See LICENSE file for full copyright and licensing details.


def migrate(cr, version):
    cr.execute('ALTER TABLE "printnode_printjob" ALTER COLUMN "printnode_id" TYPE VARCHAR(64)')
