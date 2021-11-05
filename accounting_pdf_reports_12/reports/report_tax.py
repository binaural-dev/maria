# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportTax(models.AbstractModel):
	_name = 'report.accounting_pdf_reports.report_tax'

	@api.model
	def _get_report_values(self, docids, data=None):
		if not data.get('form'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
		return {
			'data': data['form'],
			'lines': self.get_lines(data.get('form')),
		}

	def _sql_from_amls_one(self):
		sql = """SELECT "account_move_line".tax_line_id, COALESCE(SUM("account_move_line".debit-"account_move_line".credit), 0)
					FROM %s
					WHERE %s AND "account_move_line".tax_exigible GROUP BY "account_move_line".tax_line_id"""
		return sql

	def _sql_from_amls_two(self):
		sql = """SELECT r.account_tax_id, COALESCE(SUM("account_move_line".debit-"account_move_line".credit), 0)
				 FROM %s
				 INNER JOIN account_move_line_account_tax_rel r ON ("account_move_line".id = r.account_move_line_id)
				 INNER JOIN account_tax t ON (r.account_tax_id = t.id)
				 WHERE %s AND "account_move_line".tax_exigible GROUP BY r.account_tax_id"""
		return sql

	def _compute_from_amls(self, options, taxes):
		#compute the tax amount
		sql = self._sql_from_amls_one()
		tables, where_clause, where_params = self.env['account.move.line']._query_get()
		query = sql % (tables, where_clause)
		self.env.cr.execute(query, where_params)
		results = self.env.cr.fetchall()
		for result in results:
			if result[0] in taxes:
				taxes[result[0]]['tax'] = abs(result[1])

		#compute the net amount
		sql2 = self._sql_from_amls_two()
		query = sql2 % (tables, where_clause)
		self.env.cr.execute(query, where_params)
		results = self.env.cr.fetchall()
		for result in results:
			if result[0] in taxes:
				taxes[result[0]]['net'] = abs(result[1])

	def _compute_from_amls_exent(self, options, taxes):
		print("options",options) 
		#Compras

		search_domain = []
		#search_domain += [('company_id','=',self.company_id.id)]
		search_domain += [('date_register', '>=', options['date_from'])]
		search_domain += [('date_register', '<=', options['date_to'])]
		search_domain += [
			('state', 'in', ['paid', 'open', 'in_payment']),
			('type', 'in', ['in_invoice', 'in_refund', 'in_debit', 'in_contingence']),
			]
		#'cancel' no
		docs = self.env['account.invoice'].search(search_domain, order='reference asc')
		total_exent_purchase = 0.00
		total_nc_exent_purchase = 0.00
		for i in docs:
			if i.state in ['paid', 'open', 'in_payment']:
				for line in i.invoice_line_ids:
					if len(line.invoice_line_tax_ids)>0:
						if line.invoice_line_tax_ids[0].amount == 0:
							if i.type not in ['in_refund']:
								total_exent_purchase += line.price_subtotal
							else:
								total_nc_exent_purchase += line.price_subtotal
		"""move_lines = self.env['account.move.line'].sudo().search([('parent_state','=','posted'),('date','<=',options['date_to']),('date','>=',options['date_from']),('partner_id','!=',False)])
		total_exent_purchase = 0
		total_nc_exent_purchase = 0
		for ml in move_lines:
			for t in ml.tax_ids:
				if t.amount == 0 and ml.partner_id.supplier:
					#es exento
					total_exent_purchase += ml.debit
					total_nc_exent_purchase += ml.credit"""
		#Ventas
		
		"""move_lines = self.env['account.move.line'].sudo().search([('parent_state','=','posted'),('date','<=',options['date_to']),('date','>=',options['date_from']),('partner_id','!=',False)])
		total_exent_sales = 0
		total_nc_exent_sales = 0
		for ml in move_lines:
			for t in ml.tax_ids:
				if t.amount == 0 and ml.partner_id.customer:
					#es exento
					total_exent_sales += ml.credit
					total_nc_exent_sales += ml.debit"""
		search_domain_v = []
		#search_domain_v += [('company_id','=',self.company_id.id)]
		search_domain_v += [('date', '>=', options['date_from'])]
		search_domain_v += [('date', '<=', options['date_to'])]
		search_domain_v += [
			#('state', 'in', ['paid', 'open', 'in_payment']),
			('state', 'not in', ['draft']),
			('type', 'in', ['out_invoice', 'out_refund', 'out_debit', 'out_contingence']),
			]
		#'cancel' no
		docs_v = self.env['account.invoice'].search(search_domain_v, order='reference asc')
		total_exent_sales = 0.00
		total_nc_exent_sales = 0.00
		for i in docs_v:
			if i.state in ['paid', 'open', 'in_payment']:
				for line in i.invoice_line_ids:
					if len(line.invoice_line_tax_ids)>0:
						if line.invoice_line_tax_ids[0].amount == 0:
							if i.type not in ['out_refund']:
								total_exent_sales += line.price_subtotal
							else:
								total_nc_exent_sales += line.price_subtotal
		print("cantidad de facturas procesadas::::",len(docs_v))
		return (total_exent_purchase - total_nc_exent_purchase),(total_exent_sales - total_nc_exent_sales)

	def _compute_reten_period(self,options,taxes):
		total_r = 0
		retention_lines = self.env['retention_venezuela.retention_iva_line'].sudo().search([('is_retention_client','=',True),('retention_id.date_accounting','<=',options['date_to']),('retention_id.date_accounting','>=',options['date_from']),('retention_id.state','in',['emitted','corrected'])])
		for l in retention_lines:
			total_r += l.retention_amount
		return total_r


	@api.model
	def get_lines(self, options):
		taxes = {}
		for tax in self.env['account.tax'].search([('type_tax_use', '!=', 'none')]):
			if tax.children_tax_ids:
				for child in tax.children_tax_ids:
					if child.type_tax_use != 'none':
						continue
					taxes[child.id] = {'tax': 0, 'net': 0, 'name': child.name, 'type': tax.type_tax_use}
			else:
				taxes[tax.id] = {'tax': 0, 'net': 0, 'name': tax.name, 'type': tax.type_tax_use}
		self.with_context(date_from=options['date_from'], date_to=options['date_to'], strict_range=True)._compute_from_amls(options, taxes)
		groups = dict((tp, []) for tp in ['sale', 'purchase'])
		
		#add exent lines in sale and purchase
		net_purchase,net_sales = self.with_context(date_from=options['date_from'], date_to=options['date_to'], strict_range=True)._compute_from_amls_exent(options, taxes)
		
		sales_exent = {'tax': 0, 'net': net_sales, 'name': 'Ventas internas no Gravadas', 'type': ''}
		groups['sale'].append(sales_exent)
		
		sales_export = {'tax': 0, 'net': 0, 'name': 'Ventas de exportación', 'type': ''}
		groups['sale'].append(sales_export)
		

		purchase_exent = {'tax': 0, 'net': net_purchase, 'name': 'Compras internas no Gravadas', 'type': ''}
		groups['purchase'].append(purchase_exent)

		purchase_import = {'tax': 0, 'net': 0, 'name': 'Importaciones gravadas por alicuota general', 'type': ''}
		groups['purchase'].append(purchase_import)

		purchase_import_more = {'tax': 0, 'net': 0, 'name': 'Importaciones gravadas por alicuota general mas adicional', 'type': ''}
		groups['purchase'].append(purchase_import_more)

		purchase_import_reduced = {'tax': 0, 'net': 0, 'name': 'Importaciones gravadas por alicuota reducida', 'type': ''}
		groups['purchase'].append(purchase_import_reduced)
		
		for tax in taxes.values():
			if tax['tax']:
				groups[tax['type']].append(tax)
		
		sales_aditional = {'tax': 0, 'net': 0, 'name': 'Ventas internas gravadas por alicuota general mas adicional', 'type': ''}
		groups['sale'].append(sales_aditional)

		sales_reduced = {'tax': 0, 'net': 0, 'name': 'Ventas internas gravadas por alicuota reducida', 'type': ''}#
		groups['sale'].append(sales_reduced)
		

		total_sales_amount = 0
		total_sales_tax = 0
		print("groups",groups)
		for g in groups.get('sale',[]):
			total_sales_amount += g.get('net',0)
			total_sales_tax += g.get('tax',0)

		total_sales = {'tax': total_sales_tax, 'net': total_sales_amount, 'name': 'Total Ventas y debitos fiscales para efectos de determinacion', 'type': ''}#
		groups['sale'].append(total_sales)

		total_retenciones = self.with_context(date_from=options['date_from'], date_to=options['date_to'], strict_range=True)._compute_reten_period(options, taxes)

		total_reten = {'tax': 0, 'net': total_retenciones, 'name': 'Retenciones del Periodo', 'type': ''}#
		groups['sale'].append(total_reten)


		purchase_import_more_internal = {'tax': 0, 'net': 0, 'name': 'Compras internas gravadas por alicuota general mas adicional', 'type': ''}
		groups['purchase'].append(purchase_import_more_internal)

		purchase_import_more_internal = {'tax': 0, 'net': 0, 'name': 'Compras internas gravadas por alicuota reducida', 'type': ''}#
		groups['purchase'].append(purchase_import_more_internal)

		total_purchases_amount = 0
		total_purchases_tax = 0
		print("groups",groups)
		for g in groups.get('purchase',[]):
			total_purchases_amount += g.get('net',0)
			total_purchases_tax += g.get('tax',0)

		total_purch = {'tax': total_purchases_tax, 'net': total_purchases_amount, 'name': 'Total Compras y creditos fiscales del periodo', 'type': ''}#
		groups['purchase'].append(total_purch)


		return groups
