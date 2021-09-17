# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

class StockPickingInvoiceStockMove(models.Model):
	_inherit = 'stock.picking'

	@api.depends('origin')
	def _compute_foreign_currency(self):
		for record in self:
			foreign_currency_rate = foreign_currency_id = 0
			if record.origin:
				sale_id = record.env['sale.order'].search([('name', '=', record.origin)], limit=1)
				if not sale_id:
					sale_id = record.env['account.move'].search([('name', '=', record.origin)], limit=1)
				if sale_id:
					foreign_currency_id = sale_id.currency_id.id
					foreign_currency_rate = sale_id.foreign_currency_rate
			#no encontro coincidencia con el origen
			if foreign_currency_rate and foreign_currency_id == 0:
				alternate_currency = int(record.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
				foreign_currency_id = alternate_currency
				rate = self.env['res.currency.rate'].search([('currency_id', '=', foreign_currency_id),
															 ('name', '<=', fields.Date.today())], limit=1,
															order='name desc')
				foreign_currency_rate = rate.rate
			record.foreign_currency_id = foreign_currency_id
			record.foreign_currency_rate = foreign_currency_rate