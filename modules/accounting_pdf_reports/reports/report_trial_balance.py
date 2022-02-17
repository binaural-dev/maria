# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

import logging
_logger = logging.getLogger(__name__)
class ReportTrialBalance(models.AbstractModel):
	_name = 'report.accounting_pdf_reports.report_trialbalance'
	_description = 'Trial Balance Report'

	#agregado account longitude y target move
	def _get_accounts(self, accounts, display_account,account_longitude,target_move,another_currency):
		#odoo
		""" compute the balance, debit and credit for the provided accounts
			:Arguments:
				`accounts`: list of accounts record,
				`display_account`: it's used to display either all accounts or those accounts which balance is > 0
			:Returns a list of dictionary of Accounts with following key and value
				`name`: Account name,
				`code`: Account code,
				`credit`: total amount of credit,
				`debit`: total amount of debit,
				`balance`: total amount of balance,
		"""

		account_result = {}
		# Prepare sql query base on selected parameters from wizard
		tables, where_clause, where_params = self.env['account.move.line']._query_get()
		tables = tables.replace('"','')
		if not tables:
			tables = 'account_move_line'
		wheres = [""]
		if where_clause.strip():
			wheres.append(where_clause.strip())
		filters = " AND ".join(wheres)
		_logger.info("tables %s",tables)
		# compute the balance, debit and credit for the provided accounts
		if another_currency:
			request = ("SELECT account_id AS id, SUM(debit*account_move_line.foreign_currency_rate) AS debit, SUM(credit*account_move_line.foreign_currency_rate) AS credit, (SUM(debit*account_move_line.foreign_currency_rate) - SUM(credit*account_move_line.foreign_currency_rate)) AS balance" +\
					" FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
		else:	
			request = ("SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" +\
					" FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
		params = (tuple(accounts.ids),) + tuple(where_params)
		_logger.info("REQUEST %s",request)
		_logger.info("filteres de trial balance %s",filters)
		_logger.info("WHERE PARAMS %s",where_params)
		self.env.cr.execute(request, params)
		for row in self.env.cr.dictfetchall():
			account_result[row.pop('id')] = row

		_logger.info("account_result ----------------------------------------------- %s",account_result)

		# fin odoo
		#inicio personalizado
		context = dict(self._context or {})
		date_from = datetime.strptime(context.get('date_from'), "%Y-%m-%d") if context.get('date_from') else False
		date_today = datetime.now()

		#al request de salto inicial filtrar por diarios
		if another_currency:
			if target_move == 'all':
				if date_from:
					request_init = "SELECT account_id AS id, (SUM(debit*account_move_line.foreign_currency_rate) - SUM(credit*account_move_line.foreign_currency_rate)) AS init_balance FROM account_move as account_move_line__move_id,account_move_line WHERE account_id IN %s " \
								" AND account_move_line.move_id=account_move_line__move_id.id" \
								" AND account_move_line.journal_id IN %s" \
								" AND account_move_line__move_id.date < '" + str(date_from.year) + "-" + str(
						date_from.month).zfill(2) + "-01" + \
								"' GROUP BY account_id"
				else:
					filters = filters + " AND ('account_move_line'.'date' >= '" + str(date_today.year) + "-" + str(
						date_today.month).zfill(2) + "-01')"
					request_init = "SELECT account_id AS id, (SUM(debit*account_move_line.foreign_currency_rate) - SUM(credit*account_move_line.foreign_currency_rate)) AS init_balance FROM account_move as account_move_line__move_id,account_move_line WHERE account_id IN %s " \
								" AND account_move_line.move_id=account_move_line__move_id.id" \
								" AND account_move_line.journal_id IN %s" \
								" AND account_move_line__move_id.date < '" + str(date_today.year) + "-" + str(
						date_today.month).zfill(2) + "-01" + \
								"' GROUP BY account_id"
			else:
				if date_from:
					request_init = "SELECT account_id AS id, (SUM(debit*account_move_line.foreign_currency_rate) - SUM(credit*account_move_line.foreign_currency_rate)) AS init_balance FROM account_move as account_move_line__move_id,account_move_line WHERE account_id IN %s " \
								" AND account_move_line.move_id=account_move_line__move_id.id" \
								" AND account_move_line.journal_id IN %s" \
								" AND account_move_line__move_id.date < '" + str(date_from.year) + "-" + str(
						date_from.month).zfill(2) + "-01" + \
								"' AND account_move_line__move_id.state = 'posted' GROUP BY account_id"
				else:
					filters = filters + " AND ('account_move_line'.'date' > '" + str(date_today.year) + "-" + str(
						date_today.month).zfill(2) + "-01')"
					request_init = "SELECT account_id AS id, (SUM(debit*account_move_line.foreign_currency_rate) - SUM(credit*account_move_line.foreign_currency_rate)) AS init_balance FROM account_move as account_move_line__move_id,account_move_line WHERE account_id IN %s " \
								" AND account_move_line.move_id=account_move_line__move_id.id" \
								" AND account_move_line.journal_id IN %s" \
								" AND account_move_line__move_id.date < '" + str(date_today.year) + "-" + str(
						date_today.month).zfill(2) + "-01" + \
								"' AND account_move_line__move_id.state = 'posted' GROUP BY account_id"
					##
		else:
			if target_move == 'all':
				if date_from:
					request_init = "SELECT account_id AS id, (SUM(debit) - SUM(credit)) AS init_balance FROM account_move as account_move_line__move_id,account_move_line WHERE account_id IN %s " \
								" AND account_move_line.move_id=account_move_line__move_id.id" \
								" AND account_move_line.journal_id IN %s" \
								" AND account_move_line__move_id.date < '" + str(date_from.year) + "-" + str(
						date_from.month).zfill(2) + "-01" + \
								"' GROUP BY account_id"
				else:
					filters = filters + " AND ('account_move_line'.'date' >= '" + str(date_today.year) + "-" + str(
						date_today.month).zfill(2) + "-01')"
					request_init = "SELECT account_id AS id, (SUM(debit) - SUM(credit)) AS init_balance FROM account_move as account_move_line__move_id,account_move_line WHERE account_id IN %s " \
								" AND account_move_line.move_id=account_move_line__move_id.id" \
								" AND account_move_line.journal_id IN %s" \
								" AND account_move_line__move_id.date < '" + str(date_today.year) + "-" + str(
						date_today.month).zfill(2) + "-01" + \
								"' GROUP BY account_id"
			else:
				if date_from:
					request_init = "SELECT account_id AS id, (SUM(debit) - SUM(credit)) AS init_balance FROM account_move as account_move_line__move_id,account_move_line WHERE account_id IN %s " \
								" AND account_move_line.move_id=account_move_line__move_id.id" \
								" AND account_move_line.journal_id IN %s" \
								" AND account_move_line__move_id.date < '" + str(date_from.year) + "-" + str(
						date_from.month).zfill(2) + "-01" + \
								"' AND account_move_line__move_id.state = 'posted' GROUP BY account_id"
				else:
					filters = filters + " AND ('account_move_line'.'date' > '" + str(date_today.year) + "-" + str(
						date_today.month).zfill(2) + "-01')"
					request_init = "SELECT account_id AS id, (SUM(debit) - SUM(credit)) AS init_balance FROM account_move as account_move_line__move_id,account_move_line WHERE account_id IN %s " \
								" AND account_move_line.move_id=account_move_line__move_id.id" \
								" AND account_move_line.journal_id IN %s" \
								" AND account_move_line__move_id.date < '" + str(date_today.year) + "-" + str(
						date_today.month).zfill(2) + "-01" + \
								"' AND account_move_line__move_id.state = 'posted' GROUP BY account_id"
		_logger.info("CONTEXTTTTTTTTTTTTTTTTTT %s",self._context)
		#el context trae el data
		params_init = (tuple(accounts.ids),tuple(self._context.get("journal_ids")))
		self.invalidate_cache()
		self.env.cr.execute(request_init, params_init)
		result_init_balance = self.env.cr.dictfetchall()
		self.invalidate_cache()

		#fin personalizado

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
				#print("///NO esta////////")
				for result_init in result_init_balance:
					if result_init['id'] == account.id:
						print("el saldo inicial de la cuenta es",result_init['init_balance'])
						res['init_balance'] = result_init['init_balance'] or 0.0
				res['debit'] = 0.0
				res['credit'] = 0.0
				res['balance'] = res['init_balance']
			if display_account == 'all':
				#_logger.info("Comparacion de longitud : len(account.code) %s",len(account.code))
				#_logger.info("Comparacion de longitud : account_longitude %s",account_longitude)
				if int(len(account.code)) != int(account_longitude):
					#_logger.info("la longitud de la cuenta es distinto a la configurada este ira TRUE")
					res['bold'] = True
					for detail_account in self.env['account.account'].search([('code', 'ilike', account.code)]):
						#_logger.info("Comparacion de detail_account : len(account.code) %s",len(detail_account.code))
						#_logger.info("Comparacion de detail_account : account_longitude %s",account_longitude)
						if int(len(detail_account.code)) == int(account_longitude):
							#_logger.info("la longitud de la cuenta buscada es igual al ultimo nvel sumar")
							detail_code = detail_account.code[0:len(account.code)]
							if detail_account.id in account_result:
								if detail_code == account.code:
									ib = 0
									for result_init in result_init_balance:
										if result_init['id'] == detail_account.id:
											res['init_balance'] += result_init['init_balance'] or 0.0
											ib += result_init['init_balance'] or 0.0
									#_logger.info("ESTOY ACUMULANDO EN LOS BOLD------------------------------------------")
									res['debit'] += account_result[detail_account.id].get('debit')
									res['credit'] += account_result[detail_account.id].get('credit')
									res['balance'] += account_result[detail_account.id].get('balance') + ib
								else:
									if detail_code == account.code:
										for result_init in result_init_balance:
											if result_init['id'] == detail_account.id:
												res['init_balance'] += result_init['init_balance'] or 0.0
										res['balance'] = res['init_balance'] + res['debit'] - res['credit']
							else:
								#_logger.info("no esta en account result %s",detail_account.name)
								ib = 0
								for result_init in result_init_balance:
									if result_init['id'] == detail_account.id:
										res['init_balance'] += result_init['init_balance'] or 0.0
										ib += result_init['init_balance'] or 0.0
								res['balance'] += ib

				#if res['balance'] != 0:
				#	account_res.append(res)
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
		target_move = data['form'].get('target_move')


		#fin personalizado

		model = self.env.context.get('active_model')
		docs = self.env[model].browse(self.env.context.get('active_ids', []))
		display_account = data['form'].get('display_account')
		another_currency = data['form'].get('another_currency')
		#accounts = docs if model == 'account.account' else self.env['account.account'].search([])
		accounts = self.env['account.account'].search([])
		#account_res = self.with_context(data['form'].get('used_context'))._get_accounts(accounts, display_account)
		account_res, debit_total, credit_total = self.with_context(data['form'].get('used_context'))._get_accounts(accounts, display_account,account_longitude,target_move,another_currency)
		
		alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
		foreign_currency_id = False
		if alternate_currency:
			foreign_currency_id = self.env['res.currency'].sudo().browse(int(alternate_currency))
		_logger.info("foreign_currency_id %s",foreign_currency_id)
		_logger.info("another  %s",another_currency)
		return {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'Accounts': account_res,
			'debit_total': debit_total, #nuevo
			'credit_total': credit_total, #nuevo
			'another_currency':another_currency,
			'foreign_currency_id':foreign_currency_id,
		}
