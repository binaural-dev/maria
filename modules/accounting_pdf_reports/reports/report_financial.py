# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
import re
import logging
_logger = logging.getLogger(__name__)

class ReportFinancial(models.AbstractModel):
	_name = 'report.accounting_pdf_reports.report_financial'

	def _compute_account_balance(self, accounts,data):
		""" compute the balance, debit and credit for the provided accounts
		"""
		if data['another_currency']:
			mapping = {
				'balance': "COALESCE(SUM(debit*account_move_line.foreign_currency_rate),0) - COALESCE(SUM(credit*account_move_line.foreign_currency_rate), 0) as balance",
				'debit': "COALESCE(SUM(debit*account_move_line.foreign_currency_rate), 0) as debit",
				'credit': "COALESCE(SUM(credit*account_move_line.foreign_currency_rate), 0) as credit",
			}
		else:
			mapping = {
				'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
				'debit': "COALESCE(SUM(debit), 0) as debit",
				'credit': "COALESCE(SUM(credit), 0) as credit",
			}

		res = {}
		for account in accounts:
			res[account.id] = dict.fromkeys(mapping, 0.0)
		if accounts:
			tables, where_clause, where_params = self.env['account.move.line']._query_get()
			tables = tables.replace('"', '') if tables else "account_move_line"
			wheres = [""]
			if where_clause.strip():
				wheres.append(where_clause.strip())
			filters = " AND ".join(wheres)
			request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
					   " FROM " + tables + \
					   " WHERE account_id IN %s " \
							+ filters + \
					   " GROUP BY account_id"
			params = (tuple(accounts._ids),) + tuple(where_params)
			self.env.cr.execute(request, params)
			for row in self.env.cr.dictfetchall():
				res[row['id']] = row
		return res

	def _compute_report_balance(self, reports,data):
		'''returns a dictionary with key=the ID of a record and value=the credit, debit and balance amount
		   computed for this record. If the record is of type :
			   'accounts' : it's the sum of the linked accounts
			   'account_type' : it's the sum of leaf accoutns with such an account_type
			   'account_report' : it's the amount of the related report
			   'sum' : it's the sum of the children of this record (aka a 'view' record)'''
		res = {}
		fields = ['credit', 'debit', 'balance']
		for report in reports:
			if report.id in res:
				continue
			res[report.id] = dict((fn, 0.0) for fn in fields)
			if report.type == 'accounts':
				# it's the sum of the linked accounts
				res[report.id]['account'] = self._compute_account_balance(report.account_ids,data)
				for value in res[report.id]['account'].values():
					for field in fields:
						res[report.id][field] += value.get(field)
			elif report.type == 'account_type':
				# it's the sum the leaf accounts with such an account type
				accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
				res[report.id]['account'] = self._compute_account_balance(accounts,data)
				for value in res[report.id]['account'].values():
					for field in fields:
						res[report.id][field] += value.get(field)
			elif report.type == 'account_report' and report.account_report_id:
				# it's the amount of the linked report
				res2 = self._compute_report_balance(report.account_report_id,data)
				for key, value in res2.items():
					for field in fields:
						res[report.id][field] += value[field]
			elif report.type == 'sum':
				# it's the sum of the children of this account.report
				res2 = self._compute_report_balance(report.children_ids,data)
				for key, value in res2.items():
					for field in fields:
						res[report.id][field] += value[field]
		return res

	def get_account_lines(self, data):
		lines = []
		account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
		child_reports = account_report._get_children_by_order()
		res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports,data)
		account_len = int(self.env['ir.config_parameter'].sudo().get_param('account_longitude_report', default=8))
		if data['enable_filter']:
			comparison_res = self.with_context(data.get('comparison_context'))._compute_report_balance(child_reports,data)
			for report_id, value in comparison_res.items():
				res[report_id]['comp_bal'] = value['balance']
				report_acc = res[report_id].get('account')
				if report_acc:
					for account_id, val in comparison_res[report_id].get('account').items():
						report_acc[account_id]['comp_bal'] = val['balance']

		for report in child_reports:
			n = report.name
			#if n == 'Estado de Resultado':
			if n == 'Estado de resultado (Ganancias y Pérdidas)':
				#n = 'Total Ganancias y Perdidas'
				n = 'Utilidad y/o pérdida del ejercicio'
			print("report.name",n)
			vals = {
				#'name': report.name,
				'name': n,
				'balance': res[report.id]['balance'] * float(report.sign),
				'type': 'report',
				'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
				'account_type': report.type or False, #used to underline the financial report balances
			}
			if data['debit_credit']:
				vals['debit'] = res[report.id]['debit']
				vals['credit'] = res[report.id]['credit']

			if data['enable_filter']:
				vals['balance_cmp'] = res[report.id]['comp_bal'] * float(report.sign)
			lines.append(vals) 
			if report.display_detail == 'no_detail':
				#the rest of the loop is used to display the details of the financial report, so it's not needed here.
				continue

			if res[report.id].get('account'):
				sub_lines = []
				for account_id, value in res[report.id]['account'].items():
					#if there are accounts to display, we add them to the lines with a level equals to their level in
					#the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
					#financial reports for Assets, liabilities...)
					flag = False
					account = self.env['account.account'].browse(account_id)
					nro_lvl = len(account.code) if len(account.code) > 3 else 3
					for detail_account in self.env['account.account'].search([('code', 'ilike', account.code)]):
						if len(detail_account.code) == account_len:
							if detail_account.id in res[report.id]['account'].keys():
								if res[report.id]['account'][detail_account.id]['balance'] != 0:
									regex = re.search('^' + account.code, detail_account.code)
									if regex:
										flag = True
										if len(account.code) != account_len:
											value['balance'] += res[report.id]['account'][detail_account.id]['balance'] * float(report.sign)

					account = self.env['account.account'].browse(account_id)
					vals = {
						'name': account.code + ' ' + account.name,
						'balance': value['balance'] * float(report.sign) or 0.0,
						'type': 'account',
						'level': report.display_detail == 'detail_with_hierarchy' and nro_lvl,
						'account_type': account.internal_type,
					}
					if data['debit_credit']:
						vals['debit'] = value['debit']
						vals['credit'] = value['credit']
						if not account.company_id.currency_id.is_zero(vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
							flag = True
					if not account.company_id.currency_id.is_zero(vals['balance']):
						flag = True
					if data['enable_filter']:
						vals['balance_cmp'] = value['comp_bal'] * float(report.sign)
						if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
							flag = True
					if flag:
						sub_lines.append(vals)
				lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
		return lines

	@api.model
	def _get_report_values(self, docids, data=None):
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))

		model = self.env.context.get('active_model')
		docs = self.env[model].browse(self.env.context.get('active_id'))
		report_lines = self.get_account_lines(data.get('form'))
		another_currency = data['form'].get('another_currency')
		alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
		foreign_currency_id = False
		if alternate_currency:
			foreign_currency_id = self.env['res.currency'].sudo().browse(int(alternate_currency))
		_logger.info("foreign_currency_id %s",foreign_currency_id)
		account_len = int(self.env['ir.config_parameter'].sudo().get_param('account_longitude_report', default=8))
		return {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'get_account_lines': report_lines,
			'another_currency':another_currency,
			'foreign_currency_id':foreign_currency_id,
			'account_len':account_len,
		}
