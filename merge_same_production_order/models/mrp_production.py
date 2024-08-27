from odoo import fields, models, api

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model
    def merge_same_production_orders(self, ids=None):
        #THIS FUNCTION IS MEANT TO BE USED IN A CRON, DON'T USE IT INDIVIDUALLY OR IT COULD CAUSE SLOWNESS
        
        filters = [
            ('state', 'in', ['draft', 'confirmed']),
            ('bom_id', '!=', False),
        ]
        #Only manufacturing orders in either a draft or confirmed state can be merged
        #Only manufacturing orders with a Bill of Materials can be merged
        records = self.search(filters)
        if records:
            same_manufacture_orders = {}
            for production in records:
                
                if (production.product_id, production.bom_id, production.state, production.picking_type_id) in same_manufacture_orders:
                    same_manufacture_orders[(production.product_id, production.bom_id, production.state, production.picking_type_id)] += production
                else:
                    same_manufacture_orders[(production.product_id, production.bom_id, production.state, production.picking_type_id)] = production
                #You can only merge manufacturing orders of identical products with same BoM.
                #You can only merge manufacturing with the same state.
                #You can only merge manufacturing with the same operation type
                #TODO: You can only merge manufacturing orders with no additional components or by-products.
                
            for productions in same_manufacture_orders.values():
                if len(productions) > 1: #You need at least two production orders to merge them.
                    lowest_schedule_date = min(productions.mapped("date_start"))
                    now = fields.Datetime.now()
                    if lowest_schedule_date < now:
                        lowest_schedule_date = now
                    result = productions.action_merge()
                    self.env["mrp.production"].browse(result["res_id"]).sudo().write(
                        {'date_start': lowest_schedule_date}
                    )
            return True