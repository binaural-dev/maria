# -*- coding: utf-8 -*-
from odoo import models,fields,api


class ProductModelCummingInventario(models.Model):
	_name = 'product.pattern'

	name= fields.Char(String="Nombre")
	member_ids = fields.One2many('product.template', 'pattern_id')
	product_count = fields.Char(String='Cantidad de productos', compute='get_count_products', store=True)

	@api.depends('member_ids')
	def get_count_products(self):
		self.product_count = len(self.member_ids)

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

class PatternReportStock(models.Model):
	_inherit = 'stock.quant'

	pattern_id  = fields.Many2one(related='product_id.pattern_id',
		string='Modelo', store=True, readonly=True)


