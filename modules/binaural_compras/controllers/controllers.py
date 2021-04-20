# -*- coding: utf-8 -*-
# from odoo import http


# class BinauralFacturacion(http.Controller):
#     @http.route('/binaural_compras/binaural_compras/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/binaural_compras/binaural_compras/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('binaural_compras.listing', {
#             'root': '/binaural_compras/binaural_compras',
#             'objects': http.request.env['binaural_compras.binaural_compras'].search([]),
#         })

#     @http.route('/binaural_compras/binaural_compras/objects/<model("binaural_compras.binaural_compras"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('binaural_compras.object', {
#             'object': obj
#         })
