# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Sky Rocket X CFD Shop Floor',
    'version': '1.0',
    'sequence': 160,
    'category': 'Productivity',
    'depends': ['base', 'web', 'account', 'mrp', 'sale', 'mrp_workorder'],
   

    'data': [
        'views/mrp_workorders_views.xml',
        # 'view/template_inheritance_view.xml'
     
    ],
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'sr_x_custom_filter_direct_ext/static/src/**/*.js',

        ],
    }
}
