# -*- coding: utf-8 -*-
{
    'name':"Goflow Integration",
    'description': "Send your orders and shippings through Goflow and track them online",
    'category': 'Inventory/Delivery',
    'version':'1.0',
    'depends': ['sale', 'mail','delivery'],
    'data':[
        'security/ir.model.access.csv',
        "data/api_call_data.xml",
        "views/res_config_settings.xml",
        "views/sale_order_view.xml",
        "views/store_view.xml",
        "views/product_tag_view.xml",
        "views/company_view.xml",
        "views/warehouse_view.xml",
        "views/invoice_view.xml",

    ],
    'auto_install': True,
    'license': 'OEEL-1',

}
