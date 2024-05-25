# Copyright 2022 VentorTech OU
# See LICENSE file for full copyright and licensing details.

{
    'name': 'ZPL Label Designer',
    'summary': """
        Design and publish ZPL labels with easy to use interface.
    """,
    'version': '17.0.1.3.0',
    'category': 'Tools',
    "images": ["static/description/images/banner.gif"],
    'author': 'VentorTech',
    'website': 'https://ventor.tech',
    'support': 'support@ventor.tech',
    'license': 'OPL-1',
    'live_test_url': 'https://odoo.ventor.tech/',
    'price': 99.00,
    'currency': 'EUR',
    'depends': ['base', 'product', 'stock', 'product_expiry'],
    'data': [
        # Data
        'data/ir_config_parameter_data.xml',
        'data/ir_actions_server_data.xml',
        'data/label_allowed_models.xml',
        # Access rights
        'security/security.xml',
        'security/ir.model.access.csv',
        # Root menus
        'views/designer_menus.xml',
        # Views
        'views/label_designer_view.xml',
        'views/res_config_settings_views.xml',
        'wizard/product_label_layout.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'zpl_label_designer/static/src/css/**/*',
            'zpl_label_designer/static/src/js/**/*',
            'zpl_label_designer/static/src/**/*',
        ],
    },
    'installable': True,
    'application': True,
    "cloc_exclude": [
        "static/**/*.js",
    ],
    'uninstall_hook': 'uninstall_hook',
    'post_init_hook': 'post_init_hook',
}
