# -*- coding: utf-8 -*-
{
    'name':"Import sync",
    'description': "Sale orders picking are auto batched",
    'category': 'Inventory/Delivery',
    'version':'1.0',
    'depends': ['sale','delivery_goflow'],
    'data':[
        "views/import_sync.xml",

    ],
    'auto_install': True,
    'license': 'OEEL-1',

}
