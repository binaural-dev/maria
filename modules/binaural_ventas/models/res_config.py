# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettingsBinauralVentas(models.TransientModel):
	_inherit = 'res.config.settings'

	not_cost_higher_price_sale = fields.Boolean(string='No Permitir Costo Mayor o igual al Precio de venta')
	
	def set_values(self):
		super(ResConfigSettingsBinauralVentas, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param('not_cost_higher_price_sale', self.not_cost_higher_price_sale)
	

	@api.model
	def get_values(self):
		res = super(ResConfigSettingsBinauralVentas, self).get_values()
		res['not_cost_higher_price_sale'] = self.env['ir.config_parameter'].sudo().get_param('not_cost_higher_price_sale')

		return res