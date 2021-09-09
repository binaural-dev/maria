# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions

class StockScrapBinauralInventario(models.Model):
	_inherit = 'stock.scrap'

	@api.constrains('product_id', 'location_id')
	def _validate_scraps(self):
		"""Validar que la cantidad de productos a desechar sea menor o igual a la cantidad a mano"""
		if self.env['ir.config_parameter'].sudo().get_param('not_qty_on_hand_less_zero'):
			for record in self:
				quant = record.env['stock.quant'].search([('location_id', '=', record.location_id.id), ('product_id', '=', record.product_id.id)], limit=1)
				qty = record.scrap_qty
				qty_available = quant.quantity - quant.reserved_quantity
				if quant and qty > qty_available:
					raise exceptions.ValidationError("** La cantidad ingresada es mayor a la cantidad de productos disponibles (" + str(qty_available) +" disponible) ingrese una cantidad menor.**")


class ProductChangeQuantityBinauralInventario(models.TransientModel):
	_inherit = "stock.change.product.qty"

	def change_product_qty(self):
		""" Changes the Product Quantity by creating/editing corresponding quant.
		"""
		for wizard in self:
			warehouse = self.env['stock.warehouse'].search(
				[('company_id', '=', self.env.company.id)], limit=1
			)
			# Before creating a new quant, the quand `create` method will check if
			# it exists already. If it does, it'll edit its `inventory_quantity`
			# instead of create a new one.

			quant = self.env['stock.quant'].search(
				[('location_id', '=', warehouse.lot_stock_id.id), ('product_id', '=', wizard.product_id.id)], limit=1)
			if quant and wizard.new_quantity <= quant.quantity:
				raise exceptions.Warning('La cantidad ingresada es menor a la cantidad actual, ingrese una cantidad mayor.')
			self.env['stock.quant'].with_context(inventory_mode=True).create({
				'product_id': wizard.product_id.id,
				'location_id': warehouse.lot_stock_id.id,
				'inventory_quantity': wizard.new_quantity,
			})
			return {'type': 'ir.actions.act_window_close'}
