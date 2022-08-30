# Copyright 2022 VentorTech OU
# See LICENSE file for full copyright and licensing details.


def migrate(cr, version):
    cr.execute(
        'ALTER TABLE "res_company" '
        'ADD COLUMN IF NOT EXISTS "print_labels_format" VARCHAR(64)'
    )
