# -*- coding: utf-8 -*-
#############################################################################
#
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    "name": "Label Report Changes",
    "summary": "Changes for ",
    "version": "15.0.1.0.0",
    "category": 'Reporting',
    "website": "https://www.cybrosys.com",
    "description": """Order Line Images In Sale and Sale Report, odoo 14, order line images""",
    'author': 'Ashish',
    'company': 'Ashish',
    'maintainer': 'Ashish',
    "depends": [
        'mrp'
    ],
    "data": [

        'report/order_label_mo_report.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}