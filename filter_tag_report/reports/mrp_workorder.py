from odoo import models, fields, api


class FilterTagReport(models.AbstractModel):
    _name = 'report.filter_tag_report.report_invoice_template_filter'
    _description = 'Filter Tag Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Fetch work orders based on docids
        docs = self.env['mrp.workorder'].browse(docids)


        report_data = []
        for workorder in docs:
            # Initialize pack_quantity
            pack_quantity = 0
            width = 0
            length = 0
            height = 0

            if workorder.product_id:
                attributes = workorder.product_id.product_template_variant_value_ids
                for attribute in attributes:
                    attribute_name = attribute.attribute_id.name
                    attribute_value = str(attribute.name).strip()

                    if attribute_name == 'Pack Quantity':
                        pack_quantity = int(attribute_value.replace(' Pack', ''))

                    elif attribute_name == 'Filter Length':
                        clean_value = attribute_value.replace('L:', '').replace('"', '').strip()
                        length = float(clean_value)
                        if length.is_integer():
                            length = int(length)

                    elif attribute_name == 'Filter Height':
                        clean_value = attribute_value.replace('H:', '').replace('"', '').strip()
                        height = float(clean_value)
                        if height.is_integer():
                            height = int(height)

                    elif attribute_name == 'FIlter Width':
                        clean_value = attribute_value.replace('W:', '').replace('"', '').strip()
                        width = float(clean_value)
                        if width.is_integer():
                            width = int(width)

            total = workorder.qty_production * pack_quantity * 2

            report_data.append({
                'quantity': workorder.qty_production,
                'width': width,
                'length': length,
                'height': height,
                'total': total
            })

        vals = {
            'docs': report_data,
        }
        return vals
