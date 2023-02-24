# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Website Portal Design & User image on portal',
    'description': """ Website Portal Design with user image change from the portal """,
    'summary': """ Website Portal Design with user image change from the portal """,
    'category': 'Website',
    'version': '15.0.0.0',
    'author': 'Bizople Solutions Pvt. Ltd.',
    'website': 'https://www.bizople.com/',
    'depends': [
        'website',
        'sale',
    ],
    'data': [
        'views/portal_template.xml',
    ],
    'images': [
        'static/description/banner.png'
    ],
    'installable': True,
    'application': True,
    'price': 20,
    'license': 'OPL-1',
    'currency': 'EUR',


    'assets': {

        'web.assets_frontend': [
            '/website_portal_design/static/src/lib/icofont/icofont.css',
            '/website_portal_design/static/src/lib/linearicons/style.css',
            '/website_portal_design/static/src/scss/portal.scss',
            '/website_portal_design/static/src/js/user_portal.js',
            
        ],
    }
}
