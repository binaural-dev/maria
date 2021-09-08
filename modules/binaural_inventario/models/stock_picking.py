# -*- coding: utf-8 -*-

from odoo import models, fields, api,exceptions


class StockPickingBinauralInventario(models.Model):
	_inherit = 'stock.picking'

	def _default_currency_id(self):
		return self.env.ref('base.VEF').id

	foreign_currency_id = fields.Many2one('res.currency', compute='_compute_foreign_currency')
	foreign_currency_rate = fields.Monetary(string="Tasa", tracking=True, currency_field='foreign_currency_id',
											compute='_compute_foreign_currency')
	update_cost_inventory = fields.Boolean(string='Actualizar costo del producto',default=False)

	
	def action_confirm(self):
		#no aplicar para interna y compra
		#si esta activa la prohibicion
		if self.picking_type_id.code in ['outgoing','internal'] and self.env['ir.config_parameter'].sudo().get_param('not_move_qty_higher_store'):
			for sm in self.move_ids_without_package:
				quant = self.env['stock.quant'].search(
					[('location_id', '=', self.location_id.id), ('product_id', '=', sm.product_id.id)], limit=1)
				qty = sm.product_uom_qty
				if quant and qty > (quant.quantity - quant.reserved_quantity):
					raise exceptions.ValidationError(
						"** No se puede realizar la transferencia. La cantidad a transferir es mayor a la cantidad disponible en el almacen**")
		self._check_company()
		self.mapped('package_level_ids').filtered(lambda pl: pl.state == 'draft' and not pl.move_ids)._generate_moves()
		# call `_action_confirm` on every draft move
		self.mapped('move_lines')\
			.filtered(lambda move: move.state == 'draft')\
			._action_confirm()

		# run scheduler for moves forecasted to not have enough in stock
		self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))._trigger_scheduler()
		return True
		return True




	@api.depends('origin')
	def _compute_foreign_currency(self):
		for record in self:
			foreign_currency_rate = foreign_currency_id = 0
			if record.origin:
				sale_id = record.env['sale.order'].search([('name', '=', record.origin)], limit=1)
				if sale_id:
					foreign_currency_id = sale_id.currency_id.id
					foreign_currency_rate = sale_id.foreign_currency_rate
			else:
				alternate_currency = int(record.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
				foreign_currency_id = alternate_currency
				rate = self.env['res.currency.rate'].search([('currency_id', '=', foreign_currency_id),
															 ('name', '<=', fields.Date.today())], limit=1,
															order='name desc')
				foreign_currency_rate = rate.rate
			record.foreign_currency_id = foreign_currency_id
			record.foreign_currency_rate = foreign_currency_rate

	@api.constrains('move_ids_without_package')
	def _validate_transfer_qty(self):
		""" Validar que no se pueda mover mas de la cantidad disponible en almacen 
			Validar que la cantidad realizada en la transferencia no sea mayor a la Demanda inicial"""

		for record in self:
			if record.picking_type_id.code in ['outgoing','internal'] and self.env['ir.config_parameter'].sudo().get_param('not_move_qty_higher_store'):
				for sm in record.move_ids_without_package:
					quant = record.env['stock.quant'].search([('location_id', '=', record.location_id.id), ('product_id', '=', sm.product_id.id)], limit=1)
					qty = sm.product_uom_qty
					qty_done = sm.quantity_done
					if quant and qty > (quant.quantity - quant.reserved_quantity):
						raise exceptions.ValidationError("** No se puede realizar la transferencia. La cantidad a transferir es mayor a la cantidad disponible en el almacen**")
