{
    'name': 'stock onhand report',
    "author": "Skyrocket",
    'version': '1.1',
    # 'category': 'Qweb',
    'sequence': -110,
    'summary': 'stock onhand report',
    "depends": ['base', 'sale'],
    "data": [
        'security/ir.model.access.csv',

        'views/stock_onhand_view.xml',
        # 'views/stock_onhand_menu.xml',

        # 'views/custom_sales_reporting_menu.xml',
        # 'report/sales_report_action.xml',
        # 'report/sales_report_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {},
}
