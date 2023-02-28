from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.http import request

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'
    @api.returns('self')
    def _filter_visible_menus(self):
        """ Filter `self` to only keep the menu items that should be visible in
            the menu hierarchy of the current user.
            Uses a cache for speeding up the computation.
        """
        companies=self.env.user.company_ids.mapped('name')
        visible_ids = self._visible_menu_ids(request.session.debug if request else False)
        if 'Mervfilters LLC' not in companies:
            visible_ids.discard(self.env.ref('import_sync.import_sync_main_menu').id)
        return self.filtered(lambda menu: menu.id in visible_ids)
