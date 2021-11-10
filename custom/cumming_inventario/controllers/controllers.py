# -*- coding: utf-8 -*-
# from odoo import http


# class BinauralInventario(http.Controller):
#     @http.route('/binaural_inventario/binaural_inventario/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/binaural_inventario/binaural_inventario/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('binaural_inventario.listing', {
#             'root': '/binaural_inventario/binaural_inventario',
#             'objects': http.request.env['binaural_inventario.binaural_inventario'].search([]),
#         })

#     @http.route('/binaural_inventario/binaural_inventario/objects/<model("binaural_inventario.binaural_inventario"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('binaural_inventario.object', {
#             'object': obj
#         })
