from collections import namedtuple

from odoo import models

class MrpMps(models.Model):
    _inherit = "mrp.production.schedule"

    def _get_indirect_demand_tree(self):
        """ Get the tree architecture for all the BoM and BoM line that are
        related to production schedules in self. The purpose of the tree:
        - Easier traversal than with BoM and BoM lines.
        - Allow to determine the schedules evaluation order. (compute the
        schedule without indirect demand first)
        It also made the link between schedules even if some intermediate BoM
        levels are hidden. (e.g. B1 -1-> B2 -1-> B3, schedule for B1 and B3
        are linked even if the schedule for B2 does not exist.)
        Return a list of namedtuple that represent on top the schedules without
        indirect demand and on lowest leaves the schedules that are the most
        influenced by the others.
        """
        bom_by_product = self.env['mrp.bom']._bom_find(self.product_id)

        Node = namedtuple('Node', ['product', 'ratio', 'children'])
        indirect_demand_trees = {}
        product_visited = {}

        def _get_product_tree(product, ratio):
            product_tree = product_visited.get(product)
            if product_tree:
                return Node(product_tree.product, ratio, product_tree.children)

            product_tree = Node(product, ratio, [])
            product_bom = bom_by_product.get(product)
            if product not in bom_by_product and not product_bom:
                product_bom = self.env['mrp.bom']._bom_find(product)[product]
            for line in product_bom.bom_line_ids:
                if line._skip_bom_line(product):
                    continue
                if line.product_id: #---MODIFICATION--- just added conditional#
                    line_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_id)
                    bom_qty = line.bom_id.product_uom_id._compute_quantity(line.bom_id.product_qty, line.bom_id.product_tmpl_id.uom_id)
                    ratio = line_qty / bom_qty
                    tree = _get_product_tree(line.product_id, ratio)
                    product_tree.children.append(tree)
                    if line.product_id in indirect_demand_trees:
                        del indirect_demand_trees[line.product_id]
            product_visited[product] = product_tree
            return product_tree

        for product in self.mapped('product_id'):
            if product in product_visited:
                continue
            indirect_demand_trees[product] = _get_product_tree(product, 1.0)

        return [tree for tree in indirect_demand_trees.values()]