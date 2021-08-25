# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class ProductTemplateBinauralInventario(models.Model):
	_inherit = 'product.template'

	_sql_constraints = [
		(
		'default_code_unique', 'unique(default_code)', "¡La referencia interna debe ser única! Por favor, elija otro."),
	]

	available_qty = fields.Float(
		'Cantidad Disponible', compute='_compute_available_qty', compute_sudo=False, digits='Product Unit of Measure',
		store=True)

	taxes_id = fields.Many2many('account.tax', 'product_taxes_rel', 'prod_id', 'tax_id', required=True,
								help="Default taxes used when selling the product.", string='Customer Taxes',
								domain=[('type_tax_use', '=', 'sale')],
								default=lambda self: self.env.company.account_sale_tax_id)


	@api.depends('qty_available', 'outgoing_qty')
	def _compute_available_qty(self):
		for record in self:
			record.available_qty = record.qty_available - record.outgoing_qty

	def button_dummy(self):
		# TDE FIXME: this button is very interesting
		return True

