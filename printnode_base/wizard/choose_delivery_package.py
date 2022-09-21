# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.osv import expression

SECURITY_GROUP = 'printnode_base.printnode_security_group_user'


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = 'choose.delivery.package'

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'shipping_weight' in fields_list:
            measured_weight = self._measure_weight(defaults.get('picking_id'))
            if measured_weight:
                defaults['shipping_weight'] = measured_weight

        return defaults

    def _measure_weight(self, picking_id):
        # Step 1. Check if we have enabled all settings
        user = self.env.user
        if (
            not user.has_group(SECURITY_GROUP)
            or not self.env.company.scales_enabled
            or not user.scales_enabled
        ):
            return False

        # Step 2: Picking corresponds to domain from settings?
        if not self._apply_picking_domain(picking_id):
            return False

        # Step 3: Have we defined Scales in Settings
        scales = user.get_scales()
        if not scales:
            raise UserError(
                _('Scales are not defined neither on user level, no in Settings.')
            )

        # Step 4: Finally retrieve weights in Kgs and convert to lbs if needed
        total_weight = scales.get_scales_measure_kg()
        product_weight_in_lbs_param = \
            self.env['ir.config_parameter'].sudo().get_param('product.weight_in_lbs')
        if product_weight_in_lbs_param == '1':
            # Convert to lbs
            total_weight = 2.20462262185 * total_weight
        return total_weight

    def _apply_picking_domain(self, picking_id):
        """
        Get objects by id with applied domain
        """

        domain = self.env.company.scales_picking_domain
        if domain == '[]':
            return self.env['stock.picking'].browse(picking_id)
        return self.env['stock.picking'].search(
            expression.AND([[('id', '=', picking_id)], eval(domain)])
        )
