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
            print(pro)
            if self.env['product.product'].browse(pro).bom_ids:
                component = []
                for line in self.env['product.product'].browse(pro).bom_ids[0].bom_line_ids:
                    component.append({
                        'component_name': line.product_id.name,
                        'component_qty': line.product_qty * r[pro]
                    })
                product_bom.append({
                    'product_name': self.env['product.product'].browse(pro).name,
                    'components': component
                })
        data = {
            'data': product_bom
        }
        print('data', data)
        return self.env.ref('sale_component_report.action_report_sale_component').report_action(
            self,
            data=data)
