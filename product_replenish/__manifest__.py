{
    'name': 'replenish',
    'summary': """
        for mutliple product.
    """,
    'version': '15.0.1.0.0',
    'author': 'skylabs',
    'license': 'OPL-1',
    'depends': ['product','stock','base'],
    'data': [
        'security/ir.model.access.csv',
        'views/replenish_wizard.xml'
    ],
    'assets': {
        'web.assets_backend': [
            ],
        'web.assets_qweb': [

        ],
    },
    'installable': True,
    'application': True,
}
