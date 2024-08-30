{
    'name': 'stock onhand report',
    "author": "Skyrocket",
    'version': '1.1',
    # 'category': 'Qweb',
    'sequence': -110,
    'summary': 'stock onhand report',
    "depends": ['base', 'web', 'sale', 'spreadsheet'],
    "data": [
        'security/ir.model.access.csv',

        'views/stock_onhand_view.xml',
        # 'views/stock_template.xml',
        'views/stock_wizard_view.xml',
        # 'views/stock_onhand_menu.xml',

        # 'views/custom_sales_reporting_menu.xml',
        # 'report/sales_report_action.xml',
        # 'report/sales_report_template.xml',
    ],
    # 'spreadsheet.o_spreadsheet': [
    #     'stock_onhand_report/static/src/views/stock_template.xml',
    #     ('remove', 'stock_onhand_report/static/src/views/stock_template.xml'),
    # ],
    'assets': {
        'web.assets_backend': [
            'stock_onhand_report/static/src/xml/stock_template.xml',
            'stock_onhand_report/static/src/js/stock_template_action.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
