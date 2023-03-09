from odoo import fields, models


class SaleComponentReport(models.TransientModel):
    _name = 'sale.component.report'

    date_from = fields.Date()
    date_to = fields.Date()

    def action_confirm(self):
        r = {}
        product_bom = []
        done_states = self.env['sale.report']._get_done_states()
        domain = [
            ('state', 'in', done_states),
            ('product_id', '=', self.env['product.product'].search([]).ids),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ]
        for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id']):
            r[group['product_id'][0]] = group['product_uom_qty']
        for pro in r.keys():
            if self.env['product.product'].browse(pro).bom_ids:
                for line in self.env['product.product'].browse(pro).bom_ids[0].bom_line_ids:
                    product_bom.append({
                        'component_id': line.product_id.id,
                        'component_name': line.product_id.name,
                        'component_qty': line.product_qty * r[pro]
                    })
        dct = {}
        for rec in product_bom:
            if rec['component_name'] in dct:
                dct[rec['component_name']] = int(dct[rec['component_name']]) + int(rec['component_qty'])
            else:
                dct[rec['component_name']] = []
                dct[rec['component_name']] = rec['component_qty']
        data = {
            'data': dct
        }
        print(dct)
        return self.env.ref('sale_component_report.action_report_sale_component').report_action(
            self,
            data=data)
