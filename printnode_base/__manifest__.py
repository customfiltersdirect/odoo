# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo Direct Print PRO',
    'summary': """
        Print any reports or shipping labels directly to any local,
        Wi-Fi or Bluetooth printer without downloading PDF or ZPL!
    """,
    'version': '17.0.2.6.10',
    'category': 'Tools',
    "images": ["static/description/images/logo.gif"],
    'author': 'VentorTech',
    'website': 'https://ventor.tech',
    'support': 'support@ventor.tech',
    'license': 'OPL-1',
    'live_test_url': 'https://odoo.ventor.tech/',
    'price': 299.00,
    'currency': 'EUR',
    'depends': [
        'web',
        'account',
        'stock',
        'delivery',
        'stock_delivery',
        'sale',
        'purchase',
    ],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',
        # Printed Reports Data
        'reports/package_zpl_template.xml',
        # Initial Data
        'data/ir_actions_server_data.xml',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'data/printnode_scenario_action_data.xml',
        'data/printnode_format_data.xml',
        'data/printnode_paper_data.xml',
        'data/ir_config_parameter_data.xml',
        'data/printnode_action_method_data.xml',
        'data/printnode_action_button_data.xml',
        'data/printnode_scenario_data.xml',
        'data/printnode_map_action_server_data.xml',
        'data/printnode_release_data.xml',
        'data/printnode_log_type_data.xml',
        # Root menus
        'views/printnode_menus.xml',
        # Wizards
        'wizard/printnode_installer_wizard.xml',
        'wizard/product_label_layout.xml',
        'wizard/printnode_attach_universal_wizard.xml',
        'wizard/printnode_print_reports_universal_wizard.xml',
        'wizard/stock_lot_label_layout.xml',
        'wizard/printnode_print_line_reports_wizard/abstract.xml',
        'wizard/printnode_print_line_reports_wizard/stock_move.xml',
        'wizard/printnode_print_line_reports_wizard/sale_order_line.xml',
        # Model Views
        'views/printnode_release_views.xml',
        'views/printnode_account_views.xml',
        'views/printnode_computer_views.xml',
        'views/printnode_printer_views.xml',
        'views/printnode_paper_views.xml',
        'views/printnode_printjob_views.xml',
        'views/printnode_action_button_views.xml',
        'views/printnode_scenario_views.xml',
        'views/printnode_action_method_views.xml',
        'views/printnode_map_action_server_views.xml',
        'views/printnode_report_policy_views.xml',
        'views/printnode_rule_views.xml',
        'views/printnode_workstation_views.xml',
        'views/account_move_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
        'views/shipping_label_views.xml',
        'views/stock_picking_views.xml',
        'views/delivery_carrier_views.xml',
        'views/printnode_scales_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_users_views.xml',
        'views/printnode_logging_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'printnode_base/static/src/js/constants.js',
            'printnode_base/static/src/js/action_service.js',
            'printnode_base/static/src/components/*/*.js',
            'printnode_base/static/src/components/*/*.css',
            'printnode_base/static/src/components/*/*.xml',
        ],
        'web.qunit_suite_tests': [
            'printnode_base/static/tests/printnode_base_mock_server.js',
        ],
        'web.qunit_mobile_suite_tests': [
            'printnode_base/static/tests/printnode_base_mock_server.js',
        ],
    },
    'installable': True,
    'application': True,
    "cloc_exclude": [
        "data/*",
        "models/*",
        "controllers/*",
        "reports/*",
        "wizard/*",
    ]
}
