# -*- coding: utf-8 -*-
{
    'name':"Import sync",
    'description': "",
    'category': 'Sale',
    'version':'1.0',
    'depends': ['sale','delivery_goflow'],
    'data':[
        'security/ir.model.access.csv',
        "wizard/goflow_order_sync_date.xml",

        "views/import_sync.xml",

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OEEL-1',

}
