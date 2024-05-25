# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name' : 'Skylabs Pike PDF Merge',
    'author': "skylabs",
    'version':'1.0',
    'website' : 'https://www.skyrocket.com.pk',
    'category': 'Hidden/Dependency',
    'depends': ['base'],
    'description': """
Module for merging PDF from stack array.
===============================================

In OpenERP, process_from_stack can be used to add functionality to merge pdf documents.
    """,
    "external_dependencies" : {"python" : ["pikepdf"]},
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
