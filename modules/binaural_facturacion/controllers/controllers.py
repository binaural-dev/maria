# -*- coding: utf-8 -*-
# from odoo import http


# class BinauralFacturacion(http.Controller):
#     @http.route('/binaural_facturacion/binaural_facturacion/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/binaural_facturacion/binaural_facturacion/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('binaural_facturacion.listing', {
#             'root': '/binaural_facturacion/binaural_facturacion',
#             'objects': http.request.env['binaural_facturacion.binaural_facturacion'].search([]),
#         })

#     @http.route('/binaural_facturacion/binaural_facturacion/objects/<model("binaural_facturacion.binaural_facturacion"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('binaural_facturacion.object', {
#             'object': obj
#         })
