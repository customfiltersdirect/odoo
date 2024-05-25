# Copyright 2021 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval

SECURITY_GROUP = 'printnode_base.printnode_security_group_user'


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = 'choose.delivery.package'

    @api.depends('delivery_package_type_id')
    def _compute_shipping_weight(self):
        """
        Override to measure weight from scales
        """
        measured_weight = self._measure_weight(self.picking_id.id)

        if measured_weight:
            for rec in self:
                rec.shipping_weight = measured_weight
        else:
            super()._compute_shipping_weight()

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
            expression.AND([[('id', '=', picking_id)], safe_eval(domain)])
        )
