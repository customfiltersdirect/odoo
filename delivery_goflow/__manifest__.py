# -*- coding: utf-8 -*-
{
    'name':"Goflow Integration",
    'description': "Send your orders and shippings through Goflow and track them online",
    'category': 'Inventory/Delivery',
    'version':'1.0',
    'depends': ['sale', 'mail', 'delivery', 'stock_picking_batch', 'stock'],
    'data':[
        'security/ir.model.access.csv',
        "data/api_call_data.xml",
        "data/invoice_cron.xml",
        "views/res_config_settings.xml",
        "views/sale_order_view.xml",
        "views/store_view.xml",
        "views/product_tag_view.xml",
        "views/company_view.xml",
        "views/warehouse_view.xml",
        "views/invoice_view.xml",
        "views/stock_picking_batch.xml",
        "views/stock_picking_type.xml",
        "wizard/goflow_order_search.xml",

    ],
    'auto_install': True,
    'license': 'OEEL-1',

}
