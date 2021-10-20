# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from collections import OrderedDict
from datetime import datetime
import pandas as pd


class WizardCustomerAccountStatementInheritCountry(models.TransientModel):
	_inherit = "wizard.customer.account.statement"

	def customer_account_statement(self):
		dic = self.det_columns()
		search_domain = self._get_domain_invoice()
		docs = self.env['account.invoice'].search(search_domain, order='number asc')
		lista = []
		for i in docs:
			dict = OrderedDict()
			dict.update(dic)
			if i.partner_id.action_number and i.partner_id.name:
				partner_name = str(i.partner_id.action_number.number) + '-' + str(i.partner_id.name)
			dict['Cliente'] = partner_name if partner_name else ''
			dict['Nro de Doc'] = i.number or ''
			if i.date_invoice:
				f = i.date_invoice
				fn = datetime.strptime(str(f), '%Y-%m-%d')
				dict['Fecha'] = fn.strftime('%d/%m/%Y')
			else:
				dict['Fecha'] = ''
			if i.date_due:
				fd = i.date_due
				fnd = datetime.strptime(str(fd), '%Y-%m-%d')
				dict['Fecha de Vencimiento'] = fnd.strftime('%d/%m/%Y')
			else:
				dict['Fecha de Vencimiento'] = ''
			base = 0
			not_gravable = 0
			for line in i.invoice_line_ids:
				if line.invoice_line_tax_ids.amount == 0:
					not_gravable += line.price_unit * line.quantity
				else:
					base += line.price_unit * line.quantity
			if i.type not in 'out_refund':
				dict['Base imponible'] = base or 0.00
				dict['Impuesto'] = i.amount_tax or 0.00
				dict['Exento'] = not_gravable or 0.00
				dict['Total facturado'] = i.amount_total or 0.00
				dict['Total importe adeudado'] = i.residual or 0.00
				dict['Anticipo'] = 0.00
				dict['Crédito'] = 0.00
			else:
				dict['Base imponible'] = -base or 0.00
				dict['Impuesto'] = -i.amount_tax or 0.00
				dict['Exento'] = -not_gravable or 0.00
				dict['Total facturado'] = -i.amount_total or 0.00
				dict['Total importe adeudado'] = -i.residual or 0.00
				dict['Anticipo'] = 0.00
				dict['Crédito'] = 0.00
			lista.append(dict)
		search_domain_payment = self._get_domain_payment()
		docs_payment = self.env['account.payment'].search(search_domain_payment, order='id asc')
		for p in docs_payment:
			if p.is_advance:
				anticipo = p.amount
				credito = 0
				for line in p.move_line_ids:
					anticipo -= line.amount_residual
			else:
				anticipo = 0
				credito = p.amount
				for line in p.move_line_ids:
					credito -= line.amount_residual
			if anticipo > 0 or credito > 0:
				dict = OrderedDict()
				dict.update(dic)
				if p.partner_id.action_number and p.partner_id.name:
					partner_name = str(p.partner_id.action_number.number) + '-' + str(p.partner_id.name)
				dict['Cliente'] = partner_name if partner_name else ''
				dict['Nro de Doc'] = p.name or ''
				if p.payment_date:
					f = p.payment_date
					fn = datetime.strptime(str(f), '%Y-%m-%d')
					dict['Fecha'] = fn.strftime('%d/%m/%Y')
				else:
					dict['Fecha'] = ''
				dict['Fecha de Vencimiento'] = ''
				dict['Base imponible'] = 0.00
				dict['Impuesto'] = 0.00
				dict['Exento'] = 0.00
				dict['Total facturado'] = 0.00
				dict['Total importe adeudado'] = 0.00
				dict['Anticipo'] = -anticipo or 0.00
				dict['Crédito'] = -credito or 0.00
				lista.append(dict)
		search_domain_account = self._get_domain_account()
		docs_account = self.env['account.move.line'].search(search_domain_account, order='id asc')
		module_retention = self.env['ir.module.module'].sudo().search([('state', '=', 'installed'),
																('name', '=', 'retention_venezuela')])
		if module_retention:
			conf_retention = self.env['retention_venezuela.configurate'].sudo().search([], limit=1)
		for a in docs_account.filtered(
						lambda da: not da.invoice_id and not da.payment_id and not da.payment_id_advance and
								   da.credit != 0 and da.amount_residual != 0 and
								   da.journal_id.id not in [conf_retention.journal_retention_client.id,
															conf_retention.journal_retention_supplier.id]):
			dict = OrderedDict()
			dict.update(dic)
			if a.partner_id.action_number and a.partner_id.name:
				partner_name = str(a.partner_id.action_number.number) + '-' + str(a.partner_id.name)
			dict['Cliente'] = partner_name if partner_name else ''
			dict['Nro de Doc'] = a.move_id.name
			if a.date:
				f = a.date
				fn = datetime.strptime(str(f), '%Y-%m-%d')
				dict['Fecha'] = fn.strftime('%d/%m/%Y')
			else:
				dict['Fecha'] = ''
			dict['Fecha de Vencimiento'] = ''
			dict['Base imponible'] = 0.00
			dict['Impuesto'] = 0.00
			dict['Exento'] = 0.00
			dict['Total facturado'] = 0.00
			dict['Total importe adeudado'] = 0.00
			dict['Anticipo'] = 0.00
			dict['Crédito'] = a.amount_residual or 0.00
			lista.append(dict)
		lista.sort(key=lambda date: datetime.strptime(date['Fecha'], "%d/%m/%Y"))
		tabla = pd.DataFrame(lista)
		return tabla

