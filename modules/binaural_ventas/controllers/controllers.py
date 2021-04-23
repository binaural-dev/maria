# -*- coding: utf-8 -*-
# from odoo import http


# class BinauralFacturacion(http.Controller):
#     @http.route('/binaural_ventas/binaural_ventas/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/binaural_ventas/binaural_ventas/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('binaural_ventas.listing', {
#             'root': '/binaural_ventas/binaural_ventas',
#             'objects': http.request.env['binaural_ventas.binaural_ventas'].search([]),
#         })

#     @http.route('/binaural_ventas/binaural_ventas/objects/<model("binaural_ventas.binaural_ventas"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('binaural_ventas.object', {
#             'object': obj
#         })
