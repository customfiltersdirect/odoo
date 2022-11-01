# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

{
    'name': 'ZPL Label Designer',
    'summary': """
        Design and publish ZPL labels with easy to use interface.
    """,
    'version': '15.0.1.0.0',
    'category': 'Tools',
    "images": ["static/description/images/banner.gif"],
    'author': 'VentorTech',
    'website': 'https://ventor.tech',
    'support': 'support@ventor.tech',
    'license': 'OPL-1',
    'live_test_url': 'https://odoo.ventor.tech/',
    'price': 49.00,
    'currency': 'EUR',
    'depends': ['base', 'product', 'stock', 'product_expiry'],
    'data': [
        # Data
        'data/ir_config_parameter_data.xml',
        'data/ir_actions_server_data.xml',
        # Access rights
        'security/ir.model.access.csv',
        # Root menus
        'views/designer_menus.xml',
        # Views
        'views/label_designer_view.xml',
        'wizard/product_label_layout.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'zpl_label_designer/static/src/css/label_editor.css',
            'zpl_label_designer/static/src/js/libs/fabric.min.js',
            'zpl_label_designer/static/src/js/libs/fontfaceobserver.min.js',
            'zpl_label_designer/static/src/js/constants.js',
            'zpl_label_designer/static/src/js/exceptions.js',
            'zpl_label_designer/static/src/js/label_form.js',
            'zpl_label_designer/static/src/js/label_editor_field.js',
            'zpl_label_designer/static/src/js/label_preview_field.js',
            'zpl_label_designer/static/src/js/label_radio_field.js',
        ],
        'web.assets_qweb': [
            'zpl_label_designer/static/src/xml/*.xml',
        ],
    },
    'installable': True,
    'application': True,
    "cloc_exclude": [
        "**/*"
    ],
    "uninstall_hook": "uninstall_hook",
}
