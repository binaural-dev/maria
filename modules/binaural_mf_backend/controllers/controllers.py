# -*- coding: utf-8 -*-
from odoo import http

# class BinauralMaquinaFiscal(http.Controller):
#     @http.route('/binaural__maquina__fiscal/binaural__maquina__fiscal/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/binaural__maquina__fiscal/binaural__maquina__fiscal/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('binaural__maquina__fiscal.listing', {
#             'root': '/binaural__maquina__fiscal/binaural__maquina__fiscal',
#             'objects': http.request.env['binaural__maquina__fiscal.binaural__maquina__fiscal'].search([]),
#         })

#     @http.route('/binaural__maquina__fiscal/binaural__maquina__fiscal/objects/<model("binaural__maquina__fiscal.binaural__maquina__fiscal"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('binaural__maquina__fiscal.object', {
#             'object': obj
#         })