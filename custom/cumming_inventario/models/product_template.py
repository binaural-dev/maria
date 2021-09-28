# -*- coding: utf-8 -*-
from odoo import models,fields,api
import logging
_logger = logging.getLogger(__name__)


class PriceByPricelistbinauralInventario(models.Model):
	_name = 'price.by.pricelist'
	_rec_name = 'combination'

	price = fields.Float(string='Precio')
	pricelist_name = fields.Char(string='Lista de precios')
	product_template_id = fields.Many2one('product.template', string='Producto')
	combination = fields.Char(string='Combination', compute='_compute_fields_combination')
	
	@api.depends('price', 'pricelist_name')
	def _compute_fields_combination(self):
		for test in self:
			test.combination = str(test.pricelist_name) + ' ' + str(round(test.price,2))


class ProductTemplateCummingInventario(models.Model):
	_inherit = 'product.template'

	pattern_id = fields.Many2one('product.pattern',string='Modelo',tracking=True)
	fob_cost = fields.Float(string='Costo FOB',required=False,tracking=True)
	percent_dif_cost = fields.Float(string='% DIF',compute="_compute_margin_cost",store=True,tracking=True)
	standard_price = fields.Float(
		'Costo CIF', compute='_compute_standard_price',
		inverse='_set_standard_price', search='_search_standard_price',
		digits='Product Price', groups="base.group_user",
		help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
		In FIFO: value of the last unit that left the stock (automatically computed).
		Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
		Used to compute margins on sale orders.""")

	default_code = fields.Char(
		'Código', compute='_compute_default_code',
		inverse='_set_default_code', store=True,tracking=True)


	price_by_pricelist = fields.One2many('price.by.pricelist', 'product_template_id', string='Listas de precios')
	price_pricelist_names = fields.Char(string='Precios',index=True, compute="_compute_price_names")

	provider_names = fields.Char(string='Proveedor',index=True, compute="_compute_provider_names")

	price_a = fields.Float(string='Precio Lista A',compute="_compute_price_by_cumming_list")
	price_b = fields.Float(string='Precio Lista B',compute="_compute_price_by_cumming_list")
	price_c = fields.Float(string='Precio Lista C',compute="_compute_price_by_cumming_list")
	price_d = fields.Float(string='Precio Lista D',compute="_compute_price_by_cumming_list")
	#se puede hacer con campo binario y widget como pedido en caso de que se quieran dinamicas
	def _compute_price_by_cumming_list(self):
		#buscar items de lista de precios con identificador cumming y que el producto sea el actual en el for
		for product in self:
			items = self.env['product.pricelist.item'].sudo().search([('cumming_list','!=',False),('applied_on','=','1_product'),('product_tmpl_id','=',product.id)])
			#si el identificador cumming coincide poner el precio
			product.price_a = 0
			product.price_b = 0
			product.price_c = 0
			product.price_d = 0
			for i in items:
				if i.cumming_list == 'a':
					product.price_a = i.fixed_price #puede ser price en caso que no se use fixed sino alguna otra formula
				elif i.cumming_list == 'b':
					product.price_b = i.fixed_price
				elif i.cumming_list == 'c':
					product.price_c = i.fixed_price
				elif i.cumming_list == 'd':
					product.price_d = i.fixed_price
	@api.depends("price_by_pricelist")
	def _compute_price_names(self):
		for product in self:
			names = []
			for test in product.price_by_pricelist:
				if test.pricelist_name:
					names += [str(test.pricelist_name) + ' ' + str(test.price)]

			p_name = "; ".join(names)
			product.price_pricelist_names = p_name
	@api.depends("seller_ids")
	def _compute_provider_names(self):
		for product in self:
			names = []
			for partner in product.seller_ids:
				_logger.info("partner.name %s",partner.name.name)
				if partner.name:
					names += [partner.name.name]

			p_name = "; ".join(names)
			product.provider_names = p_name

	@api.onchange('list_price')
	def onchange_list_price_price_pricelist(self):
		_logger.info("llnear listadto")
		for p in self:
			price_list = []
			if p.product_variant_id:
				_logger.info("variant %s",p.product_variant_id.id)
				all_pricelist = self.env['product.pricelist'].sudo().search([])
				
				all_pricelist_price = self.env['product.pricelist'].sudo().price_get(p.product_variant_id.id,1)
				_logger.info("toda la lista %s",type(all_pricelist))
				for pr in all_pricelist:
					_logger.info("LISTA DE PRECIOS %s",pr)
					price = all_pricelist_price.get(pr.id)
					_logger.info("PRECIO %s",price)
					price_list.append(
						(
						0,0,{
						'price': price if price else 0,
						'pricelist_name':pr.name,
						}
						)
						)
				p.write({'price_by_pricelist':[(5,0,0)]})
				p.write({'price_by_pricelist':price_list})

	#falta ejecutar esta funcion cuando se agregue una nueva lista de precios o sea modificada
	def trigger_onchange_pricelist(self):
		all_products = self.env['product.template'].search([])
		for p in all_products:
			p.onchange_list_price_price_pricelist()


	@api.depends('fob_cost', 'standard_price')
	def _compute_margin_cost(self):
		#standard = cif
		for line in self:
			margin = line.standard_price - line.fob_cost
			line.percent_dif_cost = line.standard_price and margin/line.fob_cost if line.fob_cost >0  else line.standard_price