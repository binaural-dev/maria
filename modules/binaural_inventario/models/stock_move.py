from odoo import api, fields, models, _,exceptions
from odoo.exceptions import UserError,ValidationError
from odoo.tools import float_is_zero, OrderedSet


class StockMoveBinauralInventario(models.Model):
	_inherit = "stock.move"

	def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id,
								  cost):
		self.ensure_one()
		AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

		move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
		if move_lines:
			date = self._context.get('force_period_date', fields.Date.context_today(self))
			new_account_move = AccountMove.sudo().create({
				'journal_id': journal_id,
				'line_ids': move_lines,
				'date': date,
				'ref': description,
				'stock_move_id': self.id,
				'stock_valuation_layer_ids': [(6, None, [svl_id])],
				'move_type': 'entry',
				'foreign_currency_rate': self.picking_id.foreign_currency_rate,
			})
			new_account_move._post()

	@api.constrains('move_line_ids')
	def _validate_transfer_qty_done(self):
		"""Validar que la cantidad realizada en la transferencia no sea mayor a la Demanda inicial"""
		#Si esta activa la opcion de no permitir entrar en ciclo
		if self.env['ir.config_parameter'].sudo().get_param('not_qty_done_higher_initial'):
			for record in self:
				for ml in record.move_line_ids:
					qty = record.product_uom_qty
					qty_done = ml.qty_done
					#si cantidad hecha es mayor a inicial 
					if qty_done > qty:
						raise ValidationError(
							"** La cantidad realizada no debe ser mayor a la cantidad inicial, por favor cambie la cantidad realizada**")