# Copyright 2022 VentorTech OU
# See LICENSE file for full copyright and licensing details.


def migrate(cr, version):
    cr.execute(
        'ALTER TABLE "printnode_map_action_server" '
        'DROP CONSTRAINT IF EXISTS "printnode_map_action_server_model_id_uniq"'
    )
