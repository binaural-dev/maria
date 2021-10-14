# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class ProductTemplateBinauralInventario(models.Model):
	_inherit = 'product.template'

	_sql_constraints = [
		(
		'default_code_unique', 'unique(default_code)', "¡La referencia interna debe ser única! Por favor, elija otro."),
	]

	available_qty = fields.Float(
		'Disp por Vender', compute='_compute_available_qty', compute_sudo=False, digits='Product Unit of Measure',
		store=True)

	taxes_id = fields.Many2many('account.tax', 'product_taxes_rel', 'prod_id', 'tax_id', required=True,
								help="Default taxes used when selling the product.", string='Customer Taxes',
								domain=[('type_tax_use', '=', 'sale')],
								default=lambda self: self.env.company.account_sale_tax_id)

	@api.depends('qty_available', 'outgoing_qty')
	def _compute_available_qty(self):
		for record in self:
			#record.available_qty = record.qty_available - record.outgoing_qty
			#test: disponible para vender es el sin reserva de la variante asociada
			record.available_qty = record.product_variant_id.free_qty

	def button_dummy(self):
		# TDE FIXME: this button is very interesting
		return True

	@api.constrains('list_price', 'standard_price')
	def _validate_list_price(self):
		""" Validar que el precio de ventas no sea pueda ser menor que el costo"""
		if self.env['ir.config_parameter'].sudo().get_param('not_cost_higher_price'):
			for record in self:
				price = record.list_price
				cost = record.standard_price
				if price < cost:
					raise ValidationError("El precio del producto debe ser mayor al costo")

	@api.constrains('taxes_id')
	def _check_taxes_ids_len(self):
		for record in self:
			if len(record.taxes_id)>1 and self.env['ir.config_parameter'].sudo().get_param('not_multiple_tax_product'):
				raise ValidationError("Solo un impuesto es permitido")

"""	@api.onchange('qty_available')
	def _check_qty_on_hand_binaural_inventario(self):
		for record in self:
			_logger.info("DISPARO EL CANTIDAD A MANO %s",record.qty_available)
			_logger.info("self.env['ir.config_parameter'].sudo().get_param('not_qty_on_hand_less_zero') %s",self.env['ir.config_parameter'].sudo().get_param('not_qty_on_hand_less_zero'))
			if record.qty_available < 0 and self.env['ir.config_parameter'].sudo().get_param('not_qty_on_hand_less_zero'):
				raise ValidationError("La cantidad a mano no debe ser menor a cero.")

	@api.onchange('virtual_available')
	def _check_qty_on_virtual_binaural_inventario(self):
		for record in self:
			if record.virtual_available < 0 and self.env['ir.config_parameter'].sudo().get_param('not_qty_provided_less_zero'):
				raise ValidationError("La cantidad a mano no debe ser menor a cero.")"""