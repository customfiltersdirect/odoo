# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api


class Partner(models.Model):
    _inherit = 'res.partner'

    def _get_name(self):
        partner = self
        name = super(Partner, self)._get_name()
        if self._context.get('show_name_wo_parent'):
            name = partner.name + "\n" + partner._display_address(without_company=True)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
        return name
