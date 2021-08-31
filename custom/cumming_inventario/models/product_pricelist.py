# -*- coding: utf-8 -*-
from odoo import models,fields,api


class ProductPricelistCummingInventario(models.Model):
	_inherit = 'product.pricelist'


	def recompute_pricelist_by_product(self):
		self.env['product.template'].sudo().trigger_onchange_pricelist()
		return True

	"""@api.model
	def create(self,values):
		res = super(ProductPricelistCummingInventario, self).create(values)
		#trigger recalcular lista de precios por producto
		self.env['product.template'].sudo().trigger_onchange_pricelist()
		return res

	def write(self,values):
		res = super(ProductPricelistCummingInventario, self).write(values)
		#trigger recalcular lista de precios por producto
		self.env['product.template'].sudo().trigger_onchange_pricelist()
		return res"""