# -*- coding: utf-8 -*-
{
    'name': 'Create Variants Manually Button',
    'version': '1.0',
    'description':"""
    Create Variants Manually Button
    """,
    'depends': ['base', "account", 'product', 'sale', 'stock', "purchase", "purchase_stock", "mrp",  "project", "sale_project", "sale_stock", "mrp_workorder", "stock_barcode_mrp"],
    'data': [
        "security/ir.model.access.csv",
        "views/product_template_views.xml",
        "views/inherited_product_product_views.xml",
        "wizard/create_variants_overholt_wizard.xml",
    ],
    'auto_install': False,
    'license': 'OEEL-1',
}
