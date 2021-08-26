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
			test.combination = str(test.pricelist_name) + ' ' + str(test.price)


class ProductTemplateCummingInventario(models.Model):
	_inherit = 'product.template'

	pattern_id = fields.Many2one('product.pattern',string='Modelo')
	fob_cost = fields.Float(string='Costo FOB')
	percent_dif_cost = fields.Float(string='% DIF CIF y FOB')
	standard_price = fields.Float(
		'Costo CIF', compute='_compute_standard_price',
		inverse='_set_standard_price', search='_search_standard_price',
		digits='Product Price', groups="base.group_user",
		help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
		In FIFO: value of the last unit that left the stock (automatically computed).
		Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
		Used to compute margins on sale orders.""")


	price_by_pricelist = fields.One2many('price.by.pricelist', 'product_template_id', string='Listas de precios')

	@api.onchange('list_price')
	def _onchange_list_price_price_pricelist(self):
		_logger.info("llnear listadto")
		price_list = []
		for p in self:
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
		self.write({'price_by_pricelist':[(5,0,0)]})
		self.write({'price_by_pricelist':price_list})




