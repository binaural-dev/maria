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
