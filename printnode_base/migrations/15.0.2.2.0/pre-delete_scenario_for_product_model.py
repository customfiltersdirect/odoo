# Copyright 2022 VentorTech OU
# See LICENSE file for full copyright and licensing details.


def migrate(cr, version):
    cr.execute("""
        DELETE
        FROM "printnode_scenario"
        WHERE "id" IN (
        SELECT "res_id"
        FROM "ir_model_data"
        WHERE "module" = 'printnode_base'
        AND "name" IN (
        'print_product_labels_on_transfer_scenario',
        'print_single_product_label_on_transfer_scenario'))
    """)
