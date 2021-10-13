import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)
from odoo.osv import expression
from odoo.exceptions import UserError
import math
class PriceLotCummingInventario(models.TransientModel):
	_name = 'update.price.lot'

	
	action_to_do = fields.Selection([('increase', 'Incremento'), ('decrease', 'Decremento')], string="Acción",default='increase',required=True,readonly=False)
	pricelist_id = fields.Many2one('product.pricelist',string="Listas de precios",domain="[('active','=',True)]")
	date = fields.Datetime(string='Fecha de actualización', readonly=True, required=True,default=fields.Datetime.now,)
	percentage = fields.Float(string="porcentaje",digits=(5,2),required=True,default=0,readonly=False)
	filter_products = fields.Selection([
		('all', 'TODOS'),
		('category', 'LÍNEA (Categoria)'),
		('brand','MARCA'),
		('pattern','MODELO'),
		('supplier','PROVEEDOR')
	], string='Filtrar productos por',default="all")
	brand_id = fields.Many2one('product.brand',string='Marca')
	pattern_id = fields.Many2one('product.pattern',string='Modelo')
	categ_id = fields.Many2one('product.category', 'LÍNEA')
	supplier_id = fields.Many2one('res.partner', string='PROVEEDOR')
	products_list = fields.Many2many('product.pricelist.item', string='Productos')#productos,filtrar por la lista de precios elegida y el filtro


	def update_price(self):
		#pass
		if self.percentage <= 0:
			raise UserError("Porcentaje debe ser mayor a cero")
		if not self.products_list:
			raise UserError("Lista de precios es obligatoria")
		if len(self.products_list) == 0:
			raise UserError("Debe elegir al menos un producto")
		if self.pricelist_id and self.percentage:
			for i in self.products_list:
				amount = i.fixed_price * (self.percentage/100)
				if self.action_to_do == 'increase':
					new_price = i.fixed_price + amount
				else:
					new_price = (i.fixed_price - amount) if amount <= i.fixed_price else 0
				#round(new_price)
				i.write({'fixed_price':int(math.ceil(new_price))})

	@api.onchange('brand_id','pattern_id','categ_id','pricelist_id','supplier_id')
	def onchange_filters_product(self):
		products = []
		if self.pricelist_id:
			domain = [('pricelist_id','=',self.pricelist_id.id),('applied_on','=','1_product')]
			if self.brand_id and self.filter_products == 'brand':
				domain = expression.AND([domain, [('product_tmpl_id.brand_id', '=',self.brand_id.id)]])

			if self.pattern_id and self.filter_products == 'pattern':
				domain = expression.AND([domain, [('product_tmpl_id.pattern_id', '=',self.pattern_id.id)]])

			if self.categ_id and self.filter_products == 'category':
				domain = expression.AND([domain, [('product_tmpl_id.categ_id', '=',self.pattern_id.id)]])
			
			if self.supplier_id and self.filter_products == 'supplier':
				products_by_supplier = []
				sup_inf = self.env['product.supplierinfo'].sudo().search([('name.id','=',self.supplier_id.id)])
				_logger.info(sup_inf)
				_logger.info(len(sup_inf))
				for l in sup_inf:
					if l.product_tmpl_id.id not in products_by_supplier:
						products_by_supplier.append(l.product_tmpl_id.id)
				domain = expression.AND([domain, [('product_tmpl_id.id','in',products_by_supplier)]])
			#domain = {'domain': {'products_list': [('id', 'in',products)]}}
			domain = {'domain': {'products_list': domain}}
			_logger.info("DOMAIN %s",domain)
			return domain