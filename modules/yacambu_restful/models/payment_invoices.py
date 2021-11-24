from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

import logging
_logger = logging.getLogger(__name__)


class AccountPaymentYacambuRestful(models.Model):
	
	_inherit = "account.payment"

	def paymnt_invoices(self, partner_id, invoice_id, move_id):
		lines_moves=[]
		try:
			pay_term_lines = self.env['account.account'].sudo().search([('user_type_id.type','in',('receivable', 'payable'))]).ids
			
			domain = [
       			("account_id", "in", pay_term_lines),
				('move_id.state', '=', 'posted'),
				('move_id', '=', int(move_id)),
				('partner_id', '=', int(partner_id)),
				('reconciled', '=', False),
    			'|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
			]
			domain.append(('balance', '<', 0.0))
			for line in self.env['account.move.line'].search(domain):
				_logger.info('linea %s', line)
				lines_moves.append(line.id)
		except Exception as e:
			_logger.info("Error buscando lineas de pago", str(e))
    
		_logger.info("lineas de pago %s", lines_moves)
  
		for l in lines_moves:
			_logger.info('AGREGAR %s', l)
			line_account = self.env['account.move.line'].sudo().browse(int(l))
			_logger.info('hola %s', line_account)
			_logger.info("este es el monto de la linea DEL PAGO %s", abs(line_account.amount_residual_currency))
			
			domainn = [
				("account_internal_type","in", ("receivable", "payable")),
    			("move_id", "=", invoice_id),
				("reconciled", "=", False)
			]
			# invoice = self.env['account.move.line'].sudo().search_read([("move_id", "=", invoice_id)])
			# _logger.info("invoicesssssss %s", invoice)
			lines_invoice = self.env['account.move.line'].sudo().search_read(domainn)
			_logger.info('holssssis %s', lines_invoice)

			for linv in lines_invoice:
				_logger.info('este es el monto de la factura: %s', lines_invoice[0].get('amount_residual_currency'))

				try:
					if lines_invoice[0].get('amount_residual_currency') > 0.0: 
						bal = line_account.amount_residual_currency if abs(line_account.amount_residual_currency) <= abs(lines_invoice[0].get('amount_residual_currency')) else abs(lines_invoice[0].get('amount_residual_currency'))
						_logger.info("balance a mandar en el partial %s", bal)
						partials_vals_list={
							'amount': abs(bal),
							'debit_amount_currency': abs(bal),
							'credit_amount_currency': abs(bal),
							'debit_move_id': lines_invoice[0].get('id'),
							'credit_move_id': l,
						}
						_logger.info("partial %s", partials_vals_list)
						self.env['account.partial.reconcile'].create(partials_vals_list)
						_logger.info("lllll %s", l)
						return True
					else:
						_logger.info("la factura ya esta pagada")
						return False
				except Exception as e:
					_logger.info("Error buscando linea de factura %s", str(e))

	