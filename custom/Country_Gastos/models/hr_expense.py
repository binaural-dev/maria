# -*- coding: utf-8 -*-

from odoo import models, api, exceptions, fields


class HrExpenseExtendBc(models.Model):
	_inherit = 'hr.expense'
	#Gasto

	payment_mode = fields.Selection([
		("own_account", "Employee (to reimburse)"),
		("company_account", "Company")
	], default='company_account',
		states={'done': [('readonly', True)], 'post': [('readonly', True)], 'submitted': [('readonly', True)]},
		string="Paid By")

	@api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
	def _compute_state(self):
		for expense in self:
			if not expense.sheet_id or expense.sheet_id.state == 'draft':
				expense.state = "draft"
			elif expense.sheet_id.state == "cancel":
				expense.state = "refused"
			elif expense.sheet_id.state == "approve" or expense.sheet_id.state == "post":
				expense.state = "approved"
			elif not expense.sheet_id.account_move_id and expense.sheet_id.state != 'canceled':
				#dont have move_id but is not canceled
				expense.state = "reported"
			elif expense.sheet_id.state == 'canceled':
				#set draft expense if sheet is canceled
				expense.state = "draft"
			else:
				expense.state = "done"

	def _prepare_move_values(self):
		"""
		This function prepares move values related to an expense
		"""
		self.ensure_one()
		journal = self.sheet_id.bank_journal_id if self.payment_mode == 'company_account' else self.sheet_id.journal_id
		account_date = self.sheet_id.accounting_date or self.date
		move_values = {
			'journal_id': journal.id,
			'company_id': self.env.user.company_id.id,
			'date': account_date,
			'ref': self.sheet_id.name + ' - '+self.sheet_id.bank_transaction_number if self.sheet_id.bank_transaction_number else self.sheet_id.name,  # country
			# force the name to the default value, to avoid an eventual 'default_name' in the context
			# to set it to '' which cause no number to be given to the account.move when posted.
			'name': '/',
		}
		return move_values

	def action_move_create(self):
		'''
		main function that is called when trying to create the accounting entries related to an expense
		'''
		move_group_by_sheet = self._get_account_move_by_sheet()

		move_line_values_by_expense = self._get_account_move_line_values()

		for expense in self:
			company_currency = expense.company_id.currency_id
			different_currency = expense.currency_id != company_currency

			# get the account move of the related sheet
			move = move_group_by_sheet[expense.sheet_id.id]

			# get move line values
			move_line_values = move_line_values_by_expense.get(expense.id)
			move_line_dst = move_line_values[-1]
			total_amount = move_line_dst['debit'] or -move_line_dst['credit']
			total_amount_currency = move_line_dst['amount_currency']

			# create one more move line, a counterline for the total on payable account
			if expense.payment_mode == 'company_account':
				if not expense.sheet_id.bank_journal_id.default_credit_account_id:
					raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.sheet_id.bank_journal_id.name))
				journal = expense.sheet_id.bank_journal_id
				# create payment
				payment_methods = journal.outbound_payment_method_ids if total_amount < 0 else journal.inbound_payment_method_ids
				journal_currency = journal.currency_id or journal.company_id.currency_id
				payment = self.env['account.payment'].create({
					'payment_method_id': payment_methods and payment_methods[0].id or False,
					'payment_type': 'outbound' if total_amount < 0 else 'inbound',
					'partner_id': expense.employee_id.address_home_id.commercial_partner_id.id,
					'partner_type': 'supplier',
					'journal_id': journal.id,
					'payment_date': expense.date,
					'state': 'reconciled',
					'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
					'amount': abs(total_amount_currency) if different_currency else abs(total_amount),
					'name': expense.name,
					'is_expense': True,
				})
				move_line_dst['payment_id'] = payment.id

			# link move lines to move, and move to expense sheet
			move.with_context(dont_create_taxes=True).write({
				'line_ids': [(0, 0, line) for line in move_line_values]
			})
			expense.sheet_id.write({'account_move_id': move.id})

			if expense.payment_mode == 'company_account':
				expense.sheet_id.paid_expense_sheets()

		# post the moves
		for move in move_group_by_sheet.values():
			move.post()

		return move_group_by_sheet


class HrExpenseSheetExtendBc(models.Model):
	_inherit = 'hr.expense.sheet'
	#Informe de gasto




	def get_signature(self):
		config = self.env['hr_expense.signature_config'].search([('active', '=',True)],limit=1)
		if config and config.signature:
			return config.signature
		else:
			return False



	@api.model
	def _default_bank_account(self):
		journal = self.bank_journal_id if self.payment_mode == 'company_account' else self.journal_id
		if journal:
			# bank_account_id is obj ban_acc_number is related
			journal_bank_account = journal.bank_account_id.acc_number
			return journal_bank_account

	state = fields.Selection([
		('draft', 'Draft'),
		('submit', 'Submitted'),
		('approve', 'Approved'),
		('post', 'Posted'),
		('done', 'Paid'),
		('cancel', 'Refused'),
		('canceled', 'Anulado')
	], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False, default='draft', required=True, help='Expense Report State')
	
	journal_bank_account = fields.Char(
		'Cuenta bancaria', related="bank_journal_id.bank_account_id.acc_number")

	"""journal_bank_account_company = fields.Char(
		'Cuenta bancaria', related="bank_journal_id.bank_account_id.acc_number")"""

	bank_transaction_number = fields.Char(string='Nro de Transacción Bancaria')
	
	"""@api.onchange('journal_id', 'bank_journal_id')
	def _compute_bank_account_onchange(self):
		for expense in self:
			journal = expense.bank_journal_id if expense.payment_mode == 'company_account' else expense.journal_id
			if journal:
				# bank_account_id is obj ban_acc_number is related
				expense.journal_bank_account = journal.bank_account_id.acc_number"""
	
	def action_cancel(self):
		moves = self.env['account.move']
		for inv in self:
			if inv.account_move_id:
				moves += inv.account_move_id
				for l in inv.account_move_id.line_ids:
					if l.payment_id:
						l.payment_id.write({'state': 'cancelled'})
						#not cancel because cancel function unlink move parent and in this function already doing
			#unreconcile all journal items of the invoice, since the cancellation will unlink them anyway
			inv.account_move_id.line_ids.filtered(
				lambda x: x.account_id.reconcile).remove_move_reconcile()
		self.write({'state': 'canceled', 'account_move_id': False})
		#remove relationship
		for e in self.expense_line_ids:
			e.write({'sheet_id': False})

		if moves:
			# second, invalidate the move(s)
			moves.button_cancel()
			# delete the move this invoice was pointing to
			# Note that the corresponding move_lines and move_reconciles
			# will be automatically deleted too
			moves.unlink()
		# First, set the invoices as cancelled and detach the move ids

		return True
