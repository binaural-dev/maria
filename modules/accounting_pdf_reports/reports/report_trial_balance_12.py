# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class ReportTrialBalance(models.AbstractModel):
	_name = 'report.accounting_pdf_reports.report_trialbalance'

	def _get_accounts(self, accounts, display_account, target_move, account_longitude):
		""" compute the balance, debit and credit for the provided accounts
			:Arguments:
				`accounts`: list of accounts record,
				`display_account`: it's used to display either all accounts or those accounts which balance is > 0
				`target_move`: It's use o display all or posted moves
			:Returns a list of dictionary of Accounts with following key and value
				`name`: Account name,
				`code`: Account code,
				`credit`: total amount of credit,
				`debit`: total amount of debit,
				`balance`: total amount of balance,
		"""

		account_result = {}
		context = dict(self._context or {})
		# Prepare sql query base on selected parameters from wizard
		tables, where_clause, where_params = self.env['account.move.line']._query_get()
		tables = tables.replace('"','')
		if not tables:
			tables = 'account_move_line'
		wheres = [""]
		if where_clause.strip():
			wheres.append(where_clause.strip())
		filters = " AND ".join(wheres)
		# compute the balance, debit and credit for the provided accounts
		request = ("SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" +\
				   " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
		date_from = datetime.strptime(context.get('date_from'), "%Y-%m-%d") if context.get('date_from') else False
		date_today = datetime.now()

		if target_move == 'all':
			if date_from:
				request_init = "SELECT account_id AS id, (SUM(debit) - SUM(credit)) AS init_balance FROM account_move as account_move_line__move_id,account_move_line WHERE account_id IN %s " \
							   " AND account_move_line.move_id=account_move_line__move_id.id" \
							   " AND account_move_line__move_id.date < '" + str(date_from.year) + "-" + str(
					date_from.month).zfill(2) + "-01" + \
							   "' GROUP BY account_id"
			else:
				filters = filters + " AND ('account_move_line'.'date' >= '" + str(date_today.year) + "-" + str(
					date_today.month).zfill(2) + "-01')"
				request_init = "SELECT account_id AS id, (SUM(debit) - SUM(credit)) AS init_balance FROM account_move as account_move_line__move_id,account_move_line WHERE account_id IN %s " \
							   " AND account_move_line.move_id=account_move_line__move_id.id" \
							   " AND account_move_line__move_id.date < '" + str(date_today.year) + "-" + str(
					date_today.month).zfill(2) + "-01" + \
							   "' GROUP BY account_id"
		else:
			if date_from:
				request_init = "SELECT account_id AS id, (SUM(debit) - SUM(credit)) AS init_balance FROM account_move as account_move_line__move_id,account_move_line WHERE account_id IN %s " \
							   " AND account_move_line.move_id=account_move_line__move_id.id" \
							   " AND account_move_line__move_id.date < '" + str(date_from.year) + "-" + str(
					date_from.month).zfill(2) + "-01" + \
							   "' AND account_move_line__move_id.state = 'posted' GROUP BY account_id"
			else:
				filters = filters + " AND ('account_move_line'.'date' > '" + str(date_today.year) + "-" + str(
					date_today.month).zfill(2) + "-01')"
				request_init = "SELECT account_id AS id, (SUM(debit) - SUM(credit)) AS init_balance FROM account_move as account_move_line__move_id,account_move_line WHERE account_id IN %s " \
							   " AND account_move_line.move_id=account_move_line__move_id.id" \
							   " AND account_move_line__move_id.date < '" + str(date_today.year) + "-" + str(
					date_today.month).zfill(2) + "-01" + \
							   "' AND account_move_line__move_id.state = 'posted' GROUP BY account_id"

		params_init = (tuple(accounts.ids),)
		params = (tuple(accounts.ids),) + tuple(where_params)
		self.env.cr.execute(request_init, params_init)
		result_init_balance = self.env.cr.dictfetchall()
		self.invalidate_cache()
		self.env.cr.execute(request, params)
		for row in self.env.cr.dictfetchall():
			account_result[row.pop('id')] = row

		account_res = []
		debit_total = 0
		credit_total = 0
		for account in accounts:
			res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance', 'init_balance'])
			currency = account.currency_id and account.currency_id or account.company_id.currency_id
			res['code'] = account.code
			res['name'] = account.name
			res['bold'] = False
			res['init_balance'] = 0.0
			if account.id in account_result:
				for result_init in result_init_balance:
					if result_init['id'] == account.id:
						res['init_balance'] = result_init['init_balance'] or 0.0
				res['debit'] = account_result[account.id].get('debit')
				res['credit'] = account_result[account.id].get('credit')
				res['balance'] = account_result[account.id].get('balance') + res['init_balance']
				debit_total += round(account_result[account.id].get('debit'), 2)
				credit_total += round(account_result[account.id].get('credit'), 2)
			else:
				print("///NO esta////////")
				for result_init in result_init_balance:
					if result_init['id'] == account.id:
						print("el saldo inicial de la cuenta es",result_init['init_balance'])
						res['init_balance'] = result_init['init_balance'] or 0.0
				res['debit'] = 0.0
				res['credit'] = 0.0
				res['balance'] = res['init_balance']
			if display_account == 'all':

				if len(account.code) != account_longitude:
					res['bold'] = True
					for detail_account in self.env['account.account'].search([('code', 'ilike', account.code)]):
						if len(detail_account.code) == account_longitude:
							detail_code = detail_account.code[0:len(account.code)]
							if detail_account.id in account_result:
								if detail_code == account.code:
									for result_init in result_init_balance:
										if result_init['id'] == detail_account.id:
											res['init_balance'] += result_init['init_balance'] or 0.0
									res['debit'] += account_result[detail_account.id].get('debit')
									res['credit'] += account_result[detail_account.id].get('credit')
									res['balance'] += account_result[detail_account.id].get('balance')
								else:
									if detail_code == account.code:
										for result_init in result_init_balance:
											if result_init['id'] == detail_account.id:
												res['init_balance'] += result_init['init_balance'] or 0.0
										res['balance'] = res['init_balance'] + res['debit'] - res['credit']
				#if res['balance'] != 0:
				account_res.append(res)
			if display_account == 'not_zero' and not currency.is_zero(res['balance']):
				account_res.append(res)
			if display_account == 'movement' and (not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
				account_res.append(res)
		return account_res, round(debit_total, 2), round(credit_total, 2)

	@api.model
	def _get_report_values(self, docids, data=None):
		if not data.get('form') or not self.env.context.get('active_model'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
		#personalizado
		account_longitude = self.env['ir.config_parameter'].sudo().get_param('account_longitude_report')
		if not account_longitude:	
			raise UserError("Por favor configure la longitud de las cuentas contables.")
		model = self.env.context.get('active_model')
		docs = self.env[model].browse(self.env.context.get('active_ids', []))
		display_account = data['form'].get('display_account')
		target_move = data['form'].get('target_move')
		accounts = docs if model == 'account.account' else self.env['account.account'].search([])
		account_res, debit_total, credit_total = self.with_context(data['form'].get('used_context'))._get_accounts(accounts, display_account, target_move, account_longitude)
		return {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'Accounts': account_res,
			'debit_total': debit_total,
			'credit_total': credit_total
		}
