# -*- coding: utf-8 -*-
from odoo import models,fields,api
import logging
_logger = logging.getLogger(__name__)

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

class ProductPricelistItemCummingInventario(models.Model):
	_inherit = 'product.pricelist.item'
	#este es de variante
	product_cost_cumming = fields.Float(string='Costo',related="product_id.standard_price")

	product_cost_cumming_tmpl = fields.Float(string='Costo CIF',related="product_tmpl_id.standard_price",store=True)
	product_fob_cumming_tmpl = fields.Float(string='Costo Fob',related="product_tmpl_id.fob_cost",store=True)
	percent_profit = fields.Float(string='% Ganancias',compute="_compute_margin_profit",store=True)

	alternative_full = fields.Char(string='Productos full',related="product_tmpl_id.alternative_full",store=True)


	applied_on = fields.Selection([
		('3_global', 'All Products'),
		('2_product_category', 'Product Category'),
		('1_product', 'Product'),
		('0_product_variant', 'Product Variant')], "Apply On",
		default='1_product', required=True,
		help='Pricelist Item applicable on selected option')



	@api.depends('fixed_price')
	def _compute_margin_profit(self):
		#standard = cif
		for line in self:
			_logger.info("line.product_cost_cumming_tmpl %s",line.product_cost_cumming_tmpl)
			margin = line.fixed_price - line.product_cost_cumming_tmpl
			line.percent_profit = line.fixed_price and margin/line.fixed_price
