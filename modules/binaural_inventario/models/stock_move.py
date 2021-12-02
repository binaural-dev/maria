from odoo import api, fields, models, _,exceptions
from odoo.exceptions import UserError,ValidationError
from odoo.tools import float_is_zero, OrderedSet

from collections import defaultdict
import logging
_logger = logging.getLogger(__name__)

class StockMoveBinauralInventario(models.Model):
	_inherit = "stock.move"

	def _get_def_rate(self):
		alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
		foreign_currency_id = alternate_currency
		rate = self.env['res.currency.rate'].search([('currency_id', '=', foreign_currency_id),
				('name', '<=', fields.Date.today())], limit=1,
				order='name desc')
		def_rate = rate.rate if rate else 0
		return def_rate

	def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id,
								  cost):
		self.ensure_one()
		AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

		move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
		def_rate = self._get_def_rate()
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
				'foreign_currency_rate': self.picking_id.foreign_currency_rate if self.picking_id.foreign_currency_rate else def_rate,
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

	#original desde stock account
	#duda el costo promedio se calcula solo en entradas solamente, en venfood se hizo que se calculara en salidas tipo descargo
	def product_price_update_before_done(self, forced_qty=None):
		tmpl_dict = defaultdict(lambda: 0.0)
		# adapt standard price on incomming moves if the product cost_method is 'average'
		std_price_update = {}
		#is_in() = entradas
		for move in self.filtered(lambda move: move._is_in() and move.with_company(move.company_id).product_id.cost_method == 'average'):
			product_tot_qty_available = move.product_id.sudo().with_company(move.company_id).quantity_svl + tmpl_dict[move.product_id.id]
			rounding = move.product_id.uom_id.rounding

			valued_move_lines = move._get_in_move_lines()
			qty_done = 0
			for valued_move_line in valued_move_lines:
				qty_done += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)

			qty = forced_qty or qty_done
			if float_is_zero(product_tot_qty_available, precision_rounding=rounding):
				new_std_price = move._get_price_unit()
			elif float_is_zero(product_tot_qty_available + move.product_qty, precision_rounding=rounding) or \
					float_is_zero(product_tot_qty_available + qty, precision_rounding=rounding):
				new_std_price = move._get_price_unit()
			else:
				amount_unit = std_price_update.get((move.company_id.id, move.product_id.id)) or move.product_id.with_company(move.company_id).standard_price
				# Get the standard price
				#no viene de compra o venta ya que no tiene partner
				if not move.picking_id.partner_id:
					#si debe calcularse el costo promedio
					if move.picking_id.update_cost_inventory:
						#pass
						#en cargo no hay precio solo se toma en cuenta cantidad
						new_std_price = (amount_unit * product_tot_qty_available) / (product_tot_qty_available + qty)
					else:
						#si no requiere recalcular costo promedio dejar original
						#pass
						new_std_price = ((amount_unit * product_tot_qty_available) + (move._get_price_unit() * qty)) / (product_tot_qty_available + qty)
				else:
					#si tiene partner es compra o venta dejar flujo normal
					#pass
					new_std_price = ((amount_unit * product_tot_qty_available) + (move._get_price_unit() * qty)) / (product_tot_qty_available + qty)
				
				#new_std_price = ((amount_unit * product_tot_qty_available) + (move._get_price_unit() * qty)) / (product_tot_qty_available + qty)

			tmpl_dict[move.product_id.id] += qty_done
			# Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
			move.product_id.with_company(move.company_id.id).with_context(disable_auto_svl=True).sudo().write({'standard_price': new_std_price})
			std_price_update[move.company_id.id, move.product_id.id] = new_std_price

		# adapt standard price on incomming moves if the product cost_method is 'fifo'
		for move in self.filtered(lambda move:
								  move.with_company(move.company_id).product_id.cost_method == 'fifo'
								  and float_is_zero(move.product_id.sudo().quantity_svl, precision_rounding=move.product_id.uom_id.rounding)):
			move.product_id.with_company(move.company_id.id).sudo().write({'standard_price': move._get_price_unit()})