# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettingsInvoiceStockMove(models.TransientModel):
	_inherit = 'res.config.settings'

	picking_with_residual = fields.Boolean(string='Permitir generar orden de inventario desde factura con saldo deudor')
	picking_from_sale_orer = fields.Boolean(string='Permitir generar orden de inventario automatica desde pedido de ventas')


	def set_values(self):
		super(ResConfigSettingsInvoiceStockMove, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param('picking_with_residual', self.picking_with_residual)
		self.env['ir.config_parameter'].sudo().set_param('picking_from_sale_orer', self.picking_from_sale_orer)
		
	@api.model
	def get_values(self):
		res = super(ResConfigSettingsInvoiceStockMove, self).get_values()
		res['picking_with_residual'] = self.env['ir.config_parameter'].sudo().get_param('picking_with_residual')
		res['picking_from_sale_orer'] = self.env['ir.config_parameter'].sudo().get_param('picking_from_sale_orer')

		return res