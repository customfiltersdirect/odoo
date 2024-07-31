from odoo import fields, models, api, _
import itertools

import logging
_logger = logging.getLogger(__name__)

class CreateVariantsOverholt(models.TransientModel):
    _name = "create.variants.overholt"
    _description = "Create Variants Overholt Wizard"

    product_tmpl_id = fields.Many2one("product.template", required=True, string="Product")
    attribute_line_ids = fields.Many2many('overholt.attribute.line', 'wizard_tmpl_attribute_lines', copy=True, required=True, string="Product Attributes")
    product_variant_ids = fields.One2many(related="product_tmpl_id.product_variant_ids")
    number_of_variants_to_create = fields.Integer("Approximate number of new variants to create (MAXIMUM)", compute="_compute_number_of_variants_to_create")

    @api.onchange("product_tmpl_id")
    def onchage_product_tmpl_id(self):
        if self.product_tmpl_id and self.product_tmpl_id.attribute_line_ids:
            self.attribute_line_ids = False
            for attr_line in self.product_tmpl_id.attribute_line_ids:
                self.attribute_line_ids += self.attribute_line_ids.create(
                    {'attribute_id': attr_line.attribute_id.id,
                    'value_ids': False #attr_line.value_ids
                    })
                
    @api.depends("attribute_line_ids", "product_tmpl_id")
    def _compute_number_of_variants_to_create(self):
        for wizard in self:
            variants_to_create = 0
            # variants_to_unlink = Product

            tmpl_id = wizard.product_tmpl_id
            lines_without_no_variants = tmpl_id.valid_product_template_attribute_line_ids
            Product_Attribute = self.env["product.template.attribute.value"]
            for atl in wizard.attribute_line_ids:
                Product_Attribute += atl.value_ids

            all_variants = tmpl_id.with_context(active_test=False).product_variant_ids.sorted(lambda p: (p.active, -p.id))
            # Set containing existing `product.template.attribute.value` combination
            existing_variants = {
                variant.product_template_attribute_value_ids: variant for variant in all_variants
            }
            

            # Determine which product variants need to be created based on the attribute
            # configuration. If any attribute is set to generate variants dynamically, skip the
            # process.
            # Technical note: if there is no attribute, a variant is still created because
            # 'not any([])' and 'set([]) not in set([])' are True.
            if not tmpl_id.has_dynamic_attributes():
                # Iterator containing all possible `product.template.attribute.value` combination
                # The iterator is used to avoid MemoryError in case of a huge number of combination.

                
                combs = []
                for ptal in lines_without_no_variants:
                    ptav_filtered = self.env["product.template.attribute.value"]
                    for ptav in ptal.product_template_value_ids._only_active():
                        if ptav.id in Product_Attribute.ids:
                            ptav_filtered += ptav
                    if ptav_filtered:
                        combs.append(ptav_filtered)

                approximate = 1
                for comb in combs:
                    approximate *= len(comb)
                if not combs:
                    approximate = 0
                variants_to_create += approximate

            # variants_to_unlink += all_variants - current_variants_to_activate

        if variants_to_create:
            wizard.number_of_variants_to_create = variants_to_create
        else:
            wizard.number_of_variants_to_create = 0




    def create_variants(self):
        for wizard in self:
            Product = self.env["product.product"]

            variants_to_create = []
            variants_to_activate = Product
            # variants_to_unlink = Product

            tmpl_id = wizard.product_tmpl_id
            lines_without_no_variants = tmpl_id.valid_product_template_attribute_line_ids
            Product_Attribute = self.env["product.template.attribute.value"]
            for atl in wizard.attribute_line_ids:
                Product_Attribute += atl.value_ids

            all_variants = tmpl_id.with_context(active_test=False).product_variant_ids.sorted(lambda p: (p.active, -p.id))

            current_variants_to_create = []
            current_variants_to_activate = Product

            # Set containing existing `product.template.attribute.value` combination
            existing_variants = {
                variant.product_template_attribute_value_ids: variant for variant in all_variants
            }
            

            # Determine which product variants need to be created based on the attribute
            # configuration. If any attribute is set to generate variants dynamically, skip the
            # process.
            # Technical note: if there is no attribute, a variant is still created because
            # 'not any([])' and 'set([]) not in set([])' are True.
            if not tmpl_id.has_dynamic_attributes():
                # The iterator is used to avoid MemoryError in case of a huge number of combination.
                combs = []
                attributes_to_match = self.env["product.template.attribute.value"]
                for ptal in lines_without_no_variants:
                    ptav_filtered = self.env["product.template.attribute.value"]
                    for ptav in ptal.product_template_value_ids._only_active():
                        if ptav in Product_Attribute:
                            ptav_filtered += ptav
                    if ptav_filtered:
                        combs.append(ptav_filtered)
                attributes_to_match = tuple(attributes_to_match)
                all_combinations = [comb + attributes_to_match for comb in itertools.product(*combs)]

                # For each possible variant, create if it doesn't exist yet.
                for combination_tuple in all_combinations:
                    combination = self.env['product.template.attribute.value'].concat(*combination_tuple)
                    is_combination_possible = tmpl_id._is_combination_possible_by_config(combination, ignore_no_variant=False)
                    if not is_combination_possible:
                        continue
                    if combination in existing_variants:
                        current_variants_to_activate += existing_variants[combination]
                    else:
                        current_variants_to_create.append(tmpl_id._prepare_variant_values(combination))

                variants_to_create += current_variants_to_create
                variants_to_activate += current_variants_to_activate

            else:
                for variant in existing_variants.values():
                    is_combination_possible = tmpl_id._is_combination_possible_by_config(
                        combination=variant.product_template_attribute_value_ids,
                        ignore_no_variant=False,
                    )
                    if is_combination_possible:
                        current_variants_to_activate += variant
                variants_to_activate += current_variants_to_activate

            # variants_to_unlink += all_variants - current_variants_to_activate

        if variants_to_activate:
            variants_to_activate.write({'active': True})
        if variants_to_create:
            Product.create(variants_to_create)