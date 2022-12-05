# -*- coding: utf-8 -*-
# from odoo import http


# class StockBatchCustomization(http.Controller):
#     @http.route('/stock_batch_customization/stock_batch_customization', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stock_batch_customization/stock_batch_customization/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('stock_batch_customization.listing', {
#             'root': '/stock_batch_customization/stock_batch_customization',
#             'objects': http.request.env['stock_batch_customization.stock_batch_customization'].search([]),
#         })

#     @http.route('/stock_batch_customization/stock_batch_customization/objects/<model("stock_batch_customization.stock_batch_customization"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stock_batch_customization.object', {
#             'object': obj
#         })
