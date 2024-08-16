{
    'name': 'Filter Tag Report',
    "author":"skyrocket",
    'version': '1.1',
    'category': 'Invoice',
    'sequence': 10,
    'summary': 'Filter Tag Report',
    "depends":['base', 'mrp_workorder','mrp'],
    "data":[
        "reports/mrp_filter_template.xml",
        "reports/mrp_workorder_filter.xml",
    ]
}