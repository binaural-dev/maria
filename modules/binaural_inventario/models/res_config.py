# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettingsBinauralInventario(models.TransientModel):
	_inherit = 'res.config.settings'

	not_cost_higher_price = fields.Boolean(string='No Permitir Costo Mayor al Precio')
	not_qty_on_hand_less_zero = fields.Boolean(string='No Permitir Cantidad a mano menor a 0')
	not_qty_provided_less_zero = fields.Boolean(string='No Permitir Cantidad Prevista menor a 0')
	not_qty_done_higher_initial = fields.Boolean(string='No Permitir Cantidades entregadas mayor a demanda inicial')
	not_move_qty_higher_store = fields.Boolean(string='No Permitir mover mas de la cantidad disponible en almacen')
	not_multiple_tax_product = fields.Boolean(string='No Permitir que el producto pueda tener mas un impuesto asignado')

	def set_values(self):
		super(ResConfigSettingsBinauralInventario, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param('not_cost_higher_price', self.not_cost_higher_price)
		self.env['ir.config_parameter'].sudo().set_param('not_qty_on_hand_less_zero', self.not_qty_on_hand_less_zero)
		self.env['ir.config_parameter'].sudo().set_param('not_qty_provided_less_zero', self.not_qty_provided_less_zero)
		self.env['ir.config_parameter'].sudo().set_param('not_qty_done_higher_initial', self.not_qty_done_higher_initial)
		self.env['ir.config_parameter'].sudo().set_param('not_move_qty_higher_store', self.not_move_qty_higher_store)
		self.env['ir.config_parameter'].sudo().set_param('not_multiple_tax_product', self.not_multiple_tax_product)

	@api.model
	def get_values(self):
		res = super(ResConfigSettingsBinauralInventario, self).get_values()
		res['not_cost_higher_price'] = self.env['ir.config_parameter'].sudo().get_param('not_cost_higher_price')
		res['not_qty_on_hand_less_zero'] = self.env['ir.config_parameter'].sudo().get_param('not_qty_on_hand_less_zero')
		res['not_qty_provided_less_zero'] = self.env['ir.config_parameter'].sudo().get_param('not_qty_provided_less_zero')
		res['not_qty_done_higher_initial'] = self.env['ir.config_parameter'].sudo().get_param('not_qty_done_higher_initial')
		res['not_move_qty_higher_store'] = self.env['ir.config_parameter'].sudo().get_param('not_move_qty_higher_store')
		res['not_multiple_tax_product'] = self.env['ir.config_parameter'].sudo().get_param('not_multiple_tax_product')
		return res