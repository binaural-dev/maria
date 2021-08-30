# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
class StockInventoryLineBinauralInventario(models.Model):
	_inherit = 'stock.inventory.line'

	@api.onchange('product_qty')
	def _validate_transfer_qty_done(self):
		"""Validar que la cantidad real sea mayor o igual a la cantidad Teórica en el ajuste de inventario"""
		if not self.product_qty >= self.theoretical_qty and self.env['ir.config_parameter'].sudo().get_param('not_qty_on_hand_less_zero'):
			raise exceptions.ValidationError(
				"** La cantidad cantidad real debe ser mayor o igual a la cantidad Teórica**")