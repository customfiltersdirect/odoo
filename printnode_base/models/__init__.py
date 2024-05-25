# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

# This is important to load res.company first, as new attributes from this model used
# in the other models
from . import res_company
from . import printnode_mixin
from . import printnode_logger
from . import printnode_release
from . import printnode_account
from . import printnode_printer
from . import printnode_computer
from . import printnode_printjob
from . import printnode_printer_bin
from . import printnode_format
from . import printnode_paper
from . import printnode_scales
from . import printnode_action_method
from . import printnode_action_button
from . import printnode_scenario_mixin
from . import printnode_scenario
from . import printnode_scenario_action
from . import printnode_report
from . import printnode_rule
from . import shipping_label
from . import shipping_label_document
from . import printnode_map_action_server
from . import printnode_workstation
from . import printnode_base

from . import base
from . import res_config_settings
from . import res_users
from . import sale_order
from . import account_move
from . import purchase_order
from . import stock_move_line
from . import stock_picking
from . import delivery_carrier
from . import ir_cron
from . import ir_http
from . import ir_attachment
from . import stock_move
