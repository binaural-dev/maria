# -*- coding: utf-8 -*-
from odoo import models,fields,api
import logging
_logger = logging.getLogger(__name__)

class ProductPricelistCummingInventario(models.Model):
	_inherit = 'product.pricelist'

	cumming_list = fields.Selection([
		('a', 'A'),
		('b', 'B'),
		('c', 'C'),
		('d', 'D'),
	], string='Identificador de lista')
	def recompute_pricelist_by_product(self):
		self.env['product.template'].sudo().trigger_onchange_pricelist()
		return True

	def show_item_by_list(self):
		#enviar a lista de product items con domain de lista cumming
		#cumming_list
		#return self.env.ref('proandsys_rac_14.action_picking_in_team_2_ready').read()[0]
		views = [(self.env.ref('product.product_pricelist_item_tree_view').id, 'tree'), (self.env.ref('product.product_pricelist_item_form_view').id, 'form')]
		return{
		   'name': 'Productos en lista',
			'view_type': 'form',
			'view_mode': 'tree,form',
			'view_id': False,
			'res_model': 'product.pricelist.item',
			'views': views,
			'domain': [('cumming_list', '=', self.cumming_list)],
			'type': 'ir.actions.act_window',
			#'context':{'contact_display': 'partner_address', 'search_default_available': 1}
		}
class ProductPricelistItemCummingInventario(models.Model):
	_inherit = 'product.pricelist.item'
	#este es de variante
	product_cost_cumming = fields.Float(string='Costo',related="product_id.standard_price")

	product_cost_cumming_tmpl = fields.Float(string='Costo CIF',related="product_tmpl_id.standard_price",store=True)
	product_fob_cumming_tmpl = fields.Float(string='Costo Fob',related="product_tmpl_id.fob_cost",store=True)
	percent_profit = fields.Float(string='% Ganancias',compute="_compute_margin_profit",store=True)

	alternative_full = fields.Char(string='Productos full',related="product_tmpl_id.alternative_full",store=True)

	product_price_untaxed  = fields.Float(string='Precio sin iva',compute="_compute_prices_cumming",store=True)
	product_price_tax = fields.Float(string='IVA',compute="_compute_prices_cumming",store=True)

	price_list_a = fields.Float(string='Precio Mayor',compute="_compute_prices_cumming_another",store=False)
	price_list_b = fields.Float(string='Precio Detal',compute="_compute_prices_cumming_another",store=False)

	applied_on = fields.Selection([
		('3_global', 'All Products'),
		('2_product_category', 'Product Category'),
		('1_product', 'Product'),
		('0_product_variant', 'Product Variant')], "Apply On",
		default='1_product', required=True,
		help='Pricelist Item applicable on selected option')


	product_info = fields.Char(string='Producto info',compute="_compute_product_info",store=True)

	@api.depends("product_tmpl_id")
	def _compute_product_info(self):
		for product in self:
			product.product_info = str(product.product_tmpl_id.alternative_code) +" "+str(product.product_tmpl_id.alternative_manual) +" "+str(product.product_tmpl_id.default_code)+" "+str(product.product_tmpl_id.name)


	cumming_list = fields.Selection([
		('a', 'A'),
		('b', 'B'),
		('c', 'C'),
		('d', 'D'),
	], string='Identificador de lista',related="pricelist_id.cumming_list",store=True)

	def _compute_prices_cumming_another(self):
		for i in self:
			i.price_list_a = self.env['product.pricelist.item'].sudo().search([('pricelist_id.cumming_list','=','a'),('product_tmpl_id','=',i.product_tmpl_id.id)]).fixed_price
			i.price_list_b = self.env['product.pricelist.item'].sudo().search([('pricelist_id.cumming_list','=','b'),('product_tmpl_id','=',i.product_tmpl_id.id)]).fixed_price

	@api.depends('fixed_price')
	def _compute_prices_cumming(self):
		for line in self:
			line.product_price_untaxed = line.fixed_price/1.16
			line.product_price_tax = (line.fixed_price/1.16) * 0.16

	@api.depends('fixed_price','product_cost_cumming_tmpl')
	def _compute_margin_profit(self):
		#standard = cif
		for line in self:
			_logger.info("line.product_cost_cumming_tmpl %s",line.product_cost_cumming_tmpl)
			margin = line.fixed_price - line.product_cost_cumming_tmpl
			if line.product_cost_cumming_tmpl >0:
				line.percent_profit = line.fixed_price and margin/line.product_cost_cumming_tmpl if line.product_cost_cumming_tmpl > 0 else line.fixed_price
			else:
				line.percent_profit = margin
