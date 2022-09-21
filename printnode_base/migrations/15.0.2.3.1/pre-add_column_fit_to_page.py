# Copyright 2022 VentorTech OU
# See LICENSE file for full copyright and licensing details.


def migrate(cr, version):
    cr.execute(
        'ALTER TABLE "res_company" '
        'ADD COLUMN IF NOT EXISTS "printnode_fit_to_page" BOOLEAN DEFAULT FALSE'
    )
