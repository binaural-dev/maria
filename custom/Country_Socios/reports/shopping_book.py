from openerp import models, fields, api, exceptions
from collections import OrderedDict
import pandas as pd
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class BookShoppingReport(models.TransientModel):
	_inherit = 'wizard.accounting.reports'

	def _shopping_book_invoice(self):
		search_domain = self._get_domain()
		search_domain += [
			('state', 'in', ['cancel', 'paid', 'open']),
			('type', 'in', ['in_invoice', 'in_refund', 'in_debit']),
			]
		docs = self.env['account.invoice'].search(search_domain, order='reference asc')
		docs_ids = self.env['account.invoice'].search(
			search_domain, order='reference asc').ids
		print("facturas obtenidas",docs)
		dic = self.det_columns()
		lista = []
		op = 1
		for i in docs:
			if i.retention_iva_line_ids:
				dict = OrderedDict()
				dict.update(dic)
				dict['Nª de Operación'] = 0
				f = str(i.date_invoice)
				fn = datetime.strptime(f, '%Y-%m-%d')
				dict['Fecha'] = fn.strftime('%d/%m/%Y') or ''
				if i.type in 'in_invoice':
					dict['Tipo'] = 'FAC'
					dict['Nº de Factura o Nª de Doc'] = i.invoice_number
				elif i.type in 'in_refund':
					dict['Tipo'] = 'NC'
					if i.origin:
						inv = self.env['account.invoice'].sudo().search([('number','=',i.origin)],limit=1)
						if inv:
							dict['Nº de Factura o Nª de Doc'] = i.invoice_number + '\n afecta a \n' + inv.invoice_number
						else:
							dict['Nº de Factura o Nª de Doc'] = i.invoice_number

					else:
						dict['Nº de Factura o Nª de Doc'] = i.invoice_number
				else:
					dict['Tipo'] = 'ND'
					dict['Nº de Factura o Nª de Doc'] = i.invoice_number
				
				dict['Nª de Control'] = i.reference
				dict['Proveedor'] = i.partner_id.name
				dict['R.I.F'] = i.partner_id.prefix_vat + i.partner_id.vat
				if i.type in ['in_invoice'] and i.state in ['paid', 'open']:
					dict['Tipo Transacción'] = '01-REG'
				if i.type in ['in_invoice'] and i.state in ['cancel']:
					dict['Tipo Transacción'] = '03-ANU'
				if i.type in ['in_refund', 'in_debit'] and i.state in ['paid', 'open']:
					dict['Tipo Transacción'] = '02-REG'
				if i.type in ['in_refund', 'in_debit'] and i.state in ['cancel']:
					dict['Tipo Transacción'] = '03-ANU'
				if i.state in ['paid', 'open']:
					dict['Total compra más IVA'] = i.amount_total if i.type not in 'in_refund' else -i.amount_total
					puchase_with_tax_except = 0
					for line in i.invoice_line_ids:
						if line.invoice_line_tax_ids[0].amount == 0:
							puchase_with_tax_except += line.price_subtotal
					dict['Compra Exenta'] = puchase_with_tax_except if i.type not in 'in_refund' else -puchase_with_tax_except
					base = i.amount_untaxed - puchase_with_tax_except
					dict['Base'] = base if i.type not in 'in_refund' else -base
					if base > 0 and i.amount_tax:
						iva = (i.amount_tax * 100) / base
					else:
						iva = 0.00
					dict['%'] = iva
					dict['IVA'] = i.amount_tax if i.type not in 'in_refund' else -i.amount_tax
					dict['Retenido'] = 0.00
				else:
					dict['Total compra más IVA'] = 0.00
					dict['Compra Exenta'] = 0.00
					dict['Base'] = 0.00
					dict['%'] = 0.00
					dict['IVA'] = 0.00
					dict['Retenido'] = 0.00
				for imp in i.tax_line_ids.filtered(lambda r: r.name in dic.keys()):
					dict[imp.name] += imp.amount

				
				#country retention in same line
				for r in i.retention_iva_line_ids.filtered(lambda x: x.retention_id.state =='emitted'):#, 'corrected', 'cancel'
					#si retencion asociada a factura tambien esta en el mismo rango de fecha
					if r.retention_id.date_accounting >= self.date_start and r.retention_id.date_accounting <= self.date_end:
						f = str(r.retention_id.date_accounting)
						fn = datetime.strptime(f, '%Y-%m-%d')
						dict['Fecha-ret'] = fn.strftime('%d/%m/%Y') or ''
						dict['Retenido'] = r.amount_tax_ret if i.type not in 'in_refund' else -r.amount_tax_ret
						dict['Comprobante-ret'] = r.retention_id.number
					else:
						dict['Fecha-ret'] = '-'
						dict['Retenido'] = 0
						dict['Comprobante-ret'] = '-'

				if i.type in ['in_invoice','in_debit'] and i.state in ['paid', 'open']:
					dict['TT'] = '01-R'
				if i.type in ['in_refund'] and i.state in ['paid', 'open']:
					dict['TT'] = '02-R'
				if i.type in ['in_invoice','in_debit','in_refund'] and i.state in ['cancel']:
					dict['TT'] = '03-R'
				lista.append(dict)
			else:
				dict = OrderedDict()
				dict.update(dic)
				dict['Nª de Operación'] = 0
				f = str(i.date_invoice)
				fn = datetime.strptime(f, '%Y-%m-%d')
				dict['Fecha'] = fn.strftime('%d/%m/%Y') or ''
				if i.type in 'in_invoice':
					dict['Tipo'] = 'FAC'
					dict['Nº de Factura o Nª de Doc'] = i.invoice_number
				else:
					dict['Tipo'] = 'NC'
					if i.origin:
						inv = self.env['account.invoice'].sudo().search([('number','=',i.origin)],limit=1)
						if inv:
							dict['Nº de Factura o Nª de Doc'] = i.invoice_number + '\n afecta a \n' + inv.invoice_number
						else:
							dict['Nº de Factura o Nª de Doc'] = i.invoice_number

					else:
						dict['Nº de Factura o Nª de Doc'] = i.invoice_number
				
				dict['Nª de Control'] = i.reference
				dict['Proveedor'] = i.partner_id.name
				dict['R.I.F'] = i.partner_id.prefix_vat + i.partner_id.vat
				if i.type in ['in_invoice'] and i.state in ['paid', 'open']:
					dict['Tipo Transacción'] = '01-REG'
				if i.type in ['in_invoice'] and i.state in ['cancel']:
					dict['Tipo Transacción'] = '03-ANU'
				if i.type in ['in_refund', 'in_debit'] and i.state in ['paid', 'open']:
					dict['Tipo Transacción'] = '02-REG'
				if i.type in ['in_refund', 'in_debit'] and i.state in ['cancel']:
					dict['Tipo Transacción'] = '03-ANU'
				if i.state in ['paid', 'open']:
					dict['Total compra más IVA'] = i.amount_total if i.type not in 'in_refund' else -i.amount_total
					puchase_with_tax_except = 0
					for line in i.invoice_line_ids:
						if line.invoice_line_tax_ids[0].amount == 0:
							puchase_with_tax_except += line.price_subtotal
					dict['Compra Exenta'] = puchase_with_tax_except if i.type not in 'in_refund' else -puchase_with_tax_except
					base = i.amount_untaxed - puchase_with_tax_except
					dict['Base'] = base if i.type not in 'in_refund' else -base
					if base > 0 and i.amount_tax:
						iva = (i.amount_tax * 100) / base
					else:
						iva = 0.00
					dict['%'] = iva
					dict['IVA'] = i.amount_tax if i.type not in 'in_refund' else -i.amount_tax
					dict['Retenido'] = 0.00
				else:
					dict['Total compra más IVA'] = 0.00
					dict['Compra Exenta'] = 0.00
					dict['Base'] = 0.00
					dict['%'] = 0.00
					dict['IVA'] = 0.00
					dict['Retenido'] = 0.00
				for imp in i.tax_line_ids.filtered(lambda r: r.name in dic.keys()):
					dict[imp.name] += imp.amount
				
				dict['Fecha-ret'] = '-'
				dict['Comprobante-ret'] = '-'
				if i.type in ['in_invoice','in_debit'] and i.state in ['paid', 'open']:
					dict['TT'] = '01-R'
				if i.type in ['in_refund'] and i.state in ['paid', 'open']:
					dict['TT'] = '02-R'
				if i.type in ['in_invoice','in_debit','in_refund'] and i.state in ['cancel']:
					dict['TT'] = '03-R'
				lista.append(dict)

		#buscar retenciones en el periodo que no tengan factura es decir huerfanas y ponerlas al final
		docs_ret = self.env['retention_venezuela.retention_iva_line'].sudo().search([('is_retention_client','=',False),('retention_id.date_accounting','>=',self.date_start),('retention_id.date_accounting','<=',self.date_end),('retention_id.state','in',['emitted', 'corrected']),('invoice_id','not in',docs_ids)])
		print("DOCS_RET",docs_ret)
		for r in docs_ret:
			dict = OrderedDict()
			dict.update(dic)
			dict['Nª de Operación'] = 0
			f = str(r.retention_id.date_accounting)
			fn = datetime.strptime(f, '%Y-%m-%d')
			dict['Fecha'] = fn.strftime('%d/%m/%Y') or ''
			
			dict['Tipo'] = 'RIV'
	
			dict['Nº de Factura o Nª de Doc'] =  r.retention_id.number + '\n afecta a \n' + r.invoice_id.invoice_number
			dict['Nª de Control'] = r.invoice_id.reference
			dict['Proveedor'] = r.retention_id.partner_id.name
			dict['R.I.F'] = r.retention_id.partner_id.prefix_vat + r.retention_id.partner_id.vat
			if r.retention_id.state in ['emitted', 'corrected']:
				dict['Tipo Transacción'] = '01-REG'
			if r.retention_id.state in ['cancel']:
				dict['Tipo Transacción'] = '03-ANU'
			"""if r.invoice_id.type in ['in_invoice'] and r.invoice_id.state in ['paid', 'open']:
				dict['Tipo Transacción'] = '01-REG'
			if r.invoice_id.type in ['in_invoice'] and r.invoice_id.state in ['cancel']:
				dict['Tipo Transacción'] = '03-ANU'
			if r.invoice_id.type in ['in_refund', 'in_debit'] and r.invoice_id.state in ['paid', 'open']:
				dict['Tipo Transacción'] = '02-REG'
			if r.invoice_id.type in ['in_refund', 'in_debit'] and r.invoice_id.state in ['cancel']:
				dict['Tipo Transacción'] = '03-ANU'"""

			dict['Total compra más IVA'] = 0.00
			dict['Compra Exenta'] = 0.00
			dict['Base'] = 0.00
			dict['%'] = 0.00
			dict['IVA'] = 0.00
			dict['Retenido'] = 0.00
			for imp in r.invoice_id.tax_line_ids.filtered(lambda p: p.name in dic.keys()):
				dict[imp.name] += imp.amount
					
			#country retention in same line

			f = str(r.retention_id.date_accounting)
			fn = datetime.strptime(f, '%Y-%m-%d')
			dict['Fecha-ret'] = fn.strftime('%d/%m/%Y') or ''
			dict['Retenido'] = r.amount_tax_ret if i.type not in 'in_refund' else -r.amount_tax_ret
			dict['Comprobante-ret'] = r.retention_id.number
			if r.retention_id.state in ['emitted', 'corrected']:
				dict['TT'] = '01-R'
			if r.retention_id.state in ['cancel']:
				dict['TT'] = '03-R'
			lista.append(dict)

		
		print("lista final",lista)
		lista.sort(key=lambda date: datetime.strptime(date['Fecha'], "%d/%m/%Y"))
		for item in lista:
			item['Nª de Operación'] = op
			op += 1
		tabla = pd.DataFrame(lista)
		return tabla

	