from openerp import models, fields, api, exceptions, http
from collections import OrderedDict
import pandas as pd
import logging
from datetime import datetime
import xlsxwriter
from io import BytesIO
from openerp.http import request
from openerp.addons.web.controllers.main import serialize_exception, content_disposition

from io import StringIO

_logger = logging.getLogger(__name__)


class BookSaleReportCountry(models.TransientModel):
	_inherit = 'wizard.accounting.reports'

	def _sale_book_invoice(self):
		irModuleObj = self.env['ir.module.module']
		search_domain = self._get_domain()
		search_domain += [
			('state', 'not in', ['draft']),
			('type', 'in', ['out_invoice', 'out_refund']),
		]
		docs = self.env['account.invoice'].search(
			search_domain, order='number asc')
		docs_ids = self.env['account.invoice'].search(
			search_domain, order='number asc').ids
		moduleIds = irModuleObj.sudo().search(
			[
				('state', '=', 'installed'),
				('name', '=', 'bin_maquina_fiscal')
			]
		)
		if not moduleIds:
			dic = OrderedDict([
				('Nª de Operación', 0),
				('Fecha', ''),
				('Tipo', ''),
				('Nº de Factura o Nª de Doc', ''),
				('Nª de Control', ''),
				('Cliente', ''),
				('Nº de Acción', ''),
				('R.I.F', ''),
				('Tipo Transacción', ''),
				('Total ventas más IVA', 0.00),
   				('Ventas Exentas', 0.00),
				('Imponible', 0.00),
				('%', 0.00),
				('Impuesto', 0.00),
				('Retenciones', 0.00),
			])
		else:
			maq_fiscal = self.env['bin_maquina_fiscal.machine_info'].search(
				[('active', '=', True)], limit=1)
			dic = OrderedDict([
				('Nª de Operación', 0),
				('Serial de MF', ''),
				('Fecha', ''),
				('Tipo', ''),
				('Nº de Factura o Nª de Doc', ''),
				('Nª de Control', ''),
				('Cliente', ''),
				('Nº de Acción', ''),
				('R.I.F', ''),
				('Tipo Transacción', ''),
				('Total ventas más IVA', 0.00),
   				('Ventas Exentas', 0.00),
				('Imponible', 0.00),
				('%', 0.00),
				('Impuesto', 0.00),
				('Retenciones', 0.00),
			])
		lista = []
		op = 1
		for i in docs:
			amount_retention = 0.00
			#retencion de factura que tambien este en el rango de fecha
			search_domain_rt = [
				('invoice_id', '=', i.id),('retention_id.date_accounting','>=',self.date_start),('retention_id.date_accounting','<=',self.date_end)
			]
			retention_lines = self.env['retention_venezuela.retention_iva_line'].search(
				search_domain_rt)
			for x in retention_lines:
				if x.retention_id.state in ['emitted', 'corrected']:
					amount_retention += x.retention_amount
			if amount_retention > 0:
				add_retention = 2
			else:
				add_retention = 1
			is_retention = False
			k = 0
			while k < add_retention:
				dict = OrderedDict()
				dict.update(dic)
				base = 0
				not_gravable = 0
				for line in i.invoice_line_ids:
					if line.invoice_line_tax_ids.amount == 0:
						not_gravable += line.price_unit * line.quantity
					else:
						base += line.price_unit * line.quantity
				dict['Nª de Operación'] = 0
				if moduleIds:
					if maq_fiscal:
						dict['Serial de MF'] = i.serial_machine or '' #maq_fiscal.machine_serial or ''
					else:
						dict['Serial de MF'] = ''
				if not is_retention:
					f = i.date_invoice
				else:
					f = retention_lines.filtered(
						lambda inv: inv.retention_id.state in ['emitted', 'corrected'])[
						0].retention_id.date_accounting if retention_lines.filtered(
						lambda inv: inv.retention_id.state in ['emitted', 'corrected']) else ''
				fn = datetime.strptime(str(f), '%Y-%m-%d')
				dict['Fecha'] = fn.strftime('%d/%m/%Y')
				if not is_retention:
					if i.type in 'out_invoice':
						dict['Tipo'] = 'FAC'
						dict['Nº de Factura o Nª de Doc'] = i.number
					else:
						dict['Tipo'] = 'NC'
						if i.origin:
							dict['Nº de Factura o Nª de Doc'] = i.number + '\n afecta a \n' + i.origin
						else:
							dict['Nº de Factura o Nª de Doc'] = i.number
					
					dict['Nª de Control'] = i.correlative
				else:
					dict['Tipo'] = 'RIV'
					dict['Nº de Factura o Nª de Doc'] = retention_lines.filtered(
						lambda inv: inv.retention_id.state in ['emitted', 'corrected'])[
						0].retention_id.number + '\n afecta a \n' + i.number if retention_lines.filtered(
						lambda inv: inv.retention_id.state in ['emitted', 'corrected']) else ''
					dict['Nª de Control'] = ''
				dict['Cliente'] = i.partner_id.name
				dict['Nº de Acción'] = i.action_number or ''
				dict['R.I.F'] = i.partner_id.prefix_vat.upper() + i.partner_id.vat
				if not is_retention:
					if i.type in ['out_invoice'] and i.state in ['paid', 'open']:
						dict['Tipo Transacción'] = '01-REG'
					if i.type in ['out_invoice'] and i.state in ['cancel']:
						dict['Tipo Transacción'] = '03-ANU'
					if i.type in ['out_refund'] and i.state in ['paid', 'open']:
						dict['Tipo Transacción'] = '02-REG'
					if i.type in ['out_refund'] and i.state in ['cancel']:
						dict['Tipo Transacción'] = '03-ANU'
				else:
					dict['Tipo Transacción'] = '01-REG'
				if i.state in ['paid', 'open']:
					base = 0
					not_gravable = 0
					for line in i.invoice_line_ids:
						if line.invoice_line_tax_ids.amount == 0:
							not_gravable += line.price_unit * line.quantity
						else:
							base += line.price_unit * line.quantity
					if not is_retention:
						dict['Total ventas más IVA'] = i.amount_total if i.type in 'out_invoice' else -i.amount_total
						calcule_no_contrib = not_gravable
						value_no_contrib = calcule_no_contrib if i.type in 'out_invoice' else - \
							calcule_no_contrib if calcule_no_contrib > 0.00 else 0.00
						dict['Ventas Exentas'] = value_no_contrib
						dict['Imponible'] = base if i.type == 'out_invoice' else -base
						if base > 0 and i.amount_tax:
							iva = (i.amount_tax * 100) / base
						else:
							iva = 0.00
						dict['%'] = iva
						dict['Impuesto'] = i.amount_tax if i.type in 'out_invoice' else -i.amount_tax
						dict['Retenciones'] = 0.00
					else:
						dict['Total ventas más IVA'] = 0.00
						dict['Ventas Exentas'] = 0.00
						dict['Imponible'] = 0.00
						dict['%'] = 0.00
						dict['Impuesto'] = 0.00
						dict['Retenciones'] = amount_retention if i.type == 'out_invoice' else - \
							amount_retention
				else:
					dict['Total ventas más IVA'] = 0.00
					dict['Ventas Exentas'] = 0.00
					dict['Imponible'] = 0.00
					dict['%'] = 0.00
					dict['Impuesto'] = 0.00
					dict['Retenciones'] = 0.00
				for imp in i.tax_line_ids.filtered(lambda r: r.name in dic.keys()):
					dict[imp.name] += imp.amount
				lista.append(dict)
				k += 1
				is_retention = True

		#buscar lineas retenciones en el periodo y que su factura NO este en el periodo, es decir son retenciones huerfanas en el periodo
		#si tienen factura en el periodo es que ya estan en la lista
		docs_ret = self.env['retention_venezuela.retention_iva_line'].sudo().search([('is_retention_client','=',True),('retention_id.date_accounting','>=',self.date_start),('retention_id.date_accounting','<=',self.date_end),('retention_id.state','in',['emitted', 'corrected']),('invoice_id','not in',docs_ids)])
		print("DOC RETS",docs_ret)
		for r in docs_ret:
			print("retenciones huerfanas")
			print(r.name)
			dict = OrderedDict()
			dict.update(dic)
			base = 0
			not_gravable = 0
			"""for line in i.invoice_line_ids:
				if line.invoice_line_tax_ids.amount == 0:
					not_gravable += line.price_unit * line.quantity
				else:
					base += line.price_unit * line.quantity"""
			dict['Nª de Operación'] = 0
			if moduleIds:
				if maq_fiscal:
					dict['Serial de MF'] = '' #maq_fiscal.machine_serial or ''
				else:
					dict['Serial de MF'] = ''

			f = r.retention_id.date_accounting if r.retention_id.date_accounting else ''
			fn = datetime.strptime(str(f), '%Y-%m-%d')
			dict['Fecha'] = fn.strftime('%d/%m/%Y')

			dict['Tipo'] = 'RIV'
			dict['Nº de Factura o Nª de Doc'] = r.retention_id.number + '\n afecta a \n' + r.invoice_id.number  if r.retention_id.number else ''
			dict['Nª de Control'] = ''
			dict['Cliente'] = r.retention_id.partner_id.name
			dict['Nº de Acción'] = r.retention_id.partner_id.action_number.number or ''
			dict['R.I.F'] = r.retention_id.partner_id.prefix_vat.upper() + r.retention_id.partner_id.vat
			dict['Tipo Transacción'] = '01-REG'
			"""if r.invoice_id.type in ['out_invoice'] and r.invoice_id.state in ['paid', 'open']:
				dict['Tipo Transacción'] = '01-REG'
			if r.invoice_id.type in ['out_invoice'] and r.invoice_id.state in ['cancel']:
				dict['Tipo Transacción'] = '03-ANU'
			if r.invoice_id.type in ['out_refund'] and r.invoice_id.state in ['paid', 'open']:
				dict['Tipo Transacción'] = '02-REG'
			if r.invoice_id.type in ['out_refund'] and r.invoice_id.state in ['cancel']:
				dict['Tipo Transacción'] = '03-ANU'"""
			base = 0
			not_gravable = 0
			dict['Total ventas más IVA'] = 0.00
			dict['Ventas Exentas'] = 0.00
			dict['Imponible'] = 0.00
			dict['%'] = 0.00
			dict['Impuesto'] = 0.00
			dict['Retenciones'] = r.retention_amount if r.invoice_id.type == 'out_invoice' else - r.retention_amount
			for imp in r.invoice_id.tax_line_ids.filtered(lambda p: p.name in dic.keys()):
				dict[imp.name] += imp.amount
			lista.append(dict)

		
		
		lista.sort(key=lambda date: datetime.strptime(
			date['Fecha'], "%d/%m/%Y"))
		for item in lista:
			item['Nª de Operación'] = op
			op += 1
		print(lista)
		tabla = pd.DataFrame(lista)
		
		return tabla

	def _sale_book_invoice_excel(self):
		search_domain = self._get_domain()
		search_domain += [
			('state', 'not in', ['draft']),
			('type', 'in', ['out_invoice', 'out_refund']),
		]
		docs = self.env['account.invoice'].search(
			search_domain, order='number asc')
		docs_ids = self.env['account.invoice'].search(
			search_domain, order='number asc').ids
		if self.module_mf:
			maq_fiscal = self.env['bin_maquina_fiscal.machine_info'].search(
				[('active', '=', True)], limit=1)
			dic = OrderedDict([
				('Num. de Operación', 0),
				('Serial de MF', ''),
				('Fecha', ''),
				('R.I.F', ''),
				('Nombre o Razón Social', ''),
				('Nº de Acción', ''),
				('Num. Planilla de Exportación (Forma D)', ''),
				('Num. de Factura', ''),
				#('Num. de Control', ''),
				('Num. de Nota Crédito', ''),
				('Tipo Transacción', ''),
				('Num. Factura Afectada', ''),
				('Total venta más IVA', 0.00),
				('Iva por cuenta de tercero', 0.00),
				('Ventas internas no gravadas', 0.00),
				('Base Imponible', 0.00),
				('% Alícuota general', 0.00),
				('Base Imponible Alícuota Rebaja', 0.00),
				('Alícuota Rebajada', 0.00),
				('Impuesto IVA', 0.00),
				('Comprobante', ''),
				('Retenido', 0.00),

			])
		else:
			dic = OrderedDict([
				('Num. de Operación', 0),
				('Fecha', ''),
				('R.I.F', ''),
				('Nombre o Razón Social', ''),
				('Nº de Acción', ''),
				('Num. Planilla de Exportación (Forma D)', ''),
				('Num. de Factura', ''),
				#('Num. de Control', ''),
				('Num. de Nota Crédito', ''),
				('Tipo Transacción', ''),
				('Num. Factura Afectada', ''),
				('Total venta más IVA', 0.00),
				('Iva por cuenta de tercero', 0.00),
				('Ventas internas no gravadas', 0.00),
				('Base Imponible', 0.00),
				('% Alícuota general', 0.00),
				('Base Imponible Alícuota Rebaja', 0.00),
				('Alícuota Rebajada', 0.00),
				('Impuesto IVA', 0.00),
				('Comprobante', ''),
				('Retenido', 0.00),

			])
		lista = []
		_logger.info('Facturas')
		invoices_ids = docs.ids
		_logger.info(invoices_ids)
		op = 1
		for i in docs:
			amount_retention = 0.00
			search_domain_rt = [
				('invoice_id', '=', i.id),('retention_id.date_accounting','>=',self.date_start),('retention_id.date_accounting','<=',self.date_end)
			]
			retention_lines = self.env['retention_venezuela.retention_iva_line'].search(
				search_domain_rt)
			for x in retention_lines:
				if x.retention_id.state in ['emitted', 'corrected']:
					amount_retention += x.retention_amount
			if amount_retention > 0:
				add_retention = 2
			else:
				add_retention = 1
			is_retention = False
			k = 0
			while k < add_retention:
				dict = OrderedDict()
				dict.update(dic)
				dict['Num. de Operación'] = 0
				if self.module_mf:
					if maq_fiscal:
						dict['Serial de MF'] = i.serial_machine or '' #maq_fiscal.machine_serial or ''
					else:
						dict['Serial de MF'] = ''
				if not is_retention:
					f = i.date_invoice
				else:
					f = retention_lines.filtered(
						lambda inv: inv.retention_id.state in ['emitted', 'corrected'])[
						0].retention_id.date_accounting if retention_lines.filtered(
						lambda inv: inv.retention_id.state in ['emitted', 'corrected']) else ''
				fn = datetime.strptime(str(f), '%Y-%m-%d')
				dict['Fecha'] = fn.strftime('%d/%m/%Y')
				dict['R.I.F'] = i.partner_id.prefix_vat.upper() + i.partner_id.vat
				dict['Nombre o Razón Social'] = i.partner_id.name
				dict['Nº de Acción'] = i.action_number or ''
				dict['Num. Planilla de Exportación (Forma D)'] = ''
				if i.type in 'out_invoice':
					dict['Num. de Factura'] = i.number
				else:
					dict['Num. de Factura'] = ''
				#if not is_retention:
				#	dict['Num. de Control'] = i.correlative
				#else:
				#	dict['Num. de Control'] = ''
				if i.type in 'out_invoice':
					dict['Num. de Nota Crédito'] = ''
				else:
					dict['Num. de Nota Crédito'] = i.number
				if not is_retention:
					if i.type in ['out_invoice'] and i.state in ['paid', 'open']:
						dict['Tipo Transacción'] = '01-REG'
					if i.type in ['out_invoice'] and i.state in ['cancel']:
						dict['Tipo Transacción'] = '03-ANU'
					if i.type in ['out_refund'] and i.state in ['paid', 'open']:
						dict['Tipo Transacción'] = '02-REG'
					if i.type in ['out_refund'] and i.state in ['cancel']:
						dict['Tipo Transacción'] = '03-ANU'
				else:
					dict['Tipo Transacción'] = '01-REG'

				buget = self.env['sale.order'].search(
					[('name', '=', i.origin)])

				dict['Num. Factura Afectada'] = " " if buget.id else i.origin
				base = 0
				not_gravable = 0
				for line in i.invoice_line_ids:
					if line.invoice_line_tax_ids.amount == 0:
						not_gravable += line.price_unit * line.quantity
					else:
						base += line.price_unit * line.quantity
				if not is_retention:
					dict['Total venta más IVA'] = i.amount_total if i.type == 'out_invoice' else -i.amount_total
					dict['Iva por cuenta de tercero'] = 0.00
					dict['Base Imponible'] = base if i.type == 'out_invoice' else -base
					dict['Ventas internas no gravadas'] = not_gravable if i.type == 'out_invoice' else -not_gravable
					if base > 0 and i.amount_tax:
						iva = ((i.amount_tax * 100) / base) / 100
					else:
						iva = 0.00
					dict['% Alícuota general'] = iva
					dict['Base Imponible Alícuota Rebaja'] = 0.00
					dict['Alícuota Rebajada'] = 0.00
					dict['Impuesto IVA'] = i.amount_tax if i.type == 'out_invoice' else -i.amount_tax
					if retention_lines:
						dict['Comprobante'] = retention_lines.filtered(
							lambda inv: inv.retention_id.state in ['emitted', 'corrected'])[
							0].retention_id.number if retention_lines.filtered(
							lambda inv: inv.retention_id.state in ['emitted', 'corrected']) else ''
					else:
						dict['Comprobante'] = ''
					dict['Retenido'] = 0.00
				else:
					dict['Total venta más IVA'] = 0.00
					dict['Iva por cuenta de tercero'] = 0.00
					dict['Base Imponible'] = 0.00
					dict['Ventas internas no gravadas'] = 0.00
					dict['% Alícuota general'] = 0.00
					dict['Base Imponible Alícuota Rebaja'] = 0.00
					dict['Alícuota Rebajada'] = 0.00
					dict['Impuesto IVA'] = 0.00
					dict['Comprobante'] = retention_lines.filtered(
						lambda inv: inv.retention_id.state in ['emitted', 'corrected'])[
						0].retention_id.number if retention_lines.filtered(
						lambda inv: inv.retention_id.state in ['emitted', 'corrected']) else ''
					dict['Retenido'] = amount_retention if i.type == 'out_invoice' else - \
						amount_retention
				for imp in i.tax_line_ids.filtered(lambda r: r.name in dic.keys()):
					dict[imp.name] += imp.amount
				lista.append(dict)
				k += 1
				is_retention = True
		#buscar lineas retenciones en el periodo y que su factura NO este en el periodo, es decir son retenciones huerfanas en el periodo
		#si tienen factura en el periodo es que ya estan en la lista
		docs_ret = self.env['retention_venezuela.retention_iva_line'].sudo().search([('is_retention_client','=',True),('retention_id.date_accounting','>=',self.date_start),('retention_id.date_accounting','<=',self.date_end),('retention_id.state','in',['emitted', 'corrected']),('invoice_id','not in',docs_ids)])
		print("DOC RETS",docs_ret)
		for r in docs_ret:
			print("retenciones huerfanas")
			print(r.name)
			dict = OrderedDict()
			dict.update(dic)
			base = 0
			not_gravable = 0
			dict['Num. de Operación'] = 0
			if self.module_mf:
				if maq_fiscal:
					dict['Serial de MF'] = ''#maq_fiscal.machine_serial or ''
				else:
					dict['Serial de MF'] = ''

			f = r.retention_id.date_accounting if r.retention_id.date_accounting else ''
			fn = datetime.strptime(str(f), '%Y-%m-%d')
			dict['Fecha'] = fn.strftime('%d/%m/%Y')
			dict['Num. Planilla de Exportación (Forma D)'] = ''
			#dict['Tipo'] = 'RIV'
			dict['Comprobante'] = r.retention_id.number if r.retention_id.number else ''
			#dict['Nª de Control'] = ''
			dict['Num. Factura Afectada'] = r.invoice_id.number if r.invoice_id.number else ''
			dict['Nombre o Razón Social'] = r.retention_id.partner_id.name
			dict['Nº de Acción'] = r.retention_id.partner_id.action_number.number or ''
			dict['R.I.F'] = r.retention_id.partner_id.prefix_vat.upper() + r.retention_id.partner_id.vat

			dict['Tipo Transacción'] = '01-REG'
			"""if r.invoice_id.type in ['out_invoice'] and r.invoice_id.state in ['paid', 'open']:
				dict['Tipo Transacción'] = '01-REG'
			if r.invoice_id.type in ['out_invoice'] and r.invoice_id.state in ['cancel']:
				dict['Tipo Transacción'] = '03-ANU'
			if r.invoice_id.type in ['out_refund'] and r.invoice_id.state in ['paid', 'open']:
				dict['Tipo Transacción'] = '02-REG'
			if r.invoice_id.type in ['out_refund'] and r.invoice_id.state in ['cancel']:
				dict['Tipo Transacción'] = '03-ANU'"""
			base = 0
			not_gravable = 0
			
			"""dict['Total ventas más IVA'] = 0.00
			dict['Ventas Exentas'] = 0.00
			dict['Imponible'] = 0.00
			dict['%'] = 0.00
			dict['Impuesto IVA'] = 0.00"""
			dict['Retenido'] = r.retention_amount if r.invoice_id.type == 'out_invoice' else - r.retention_amount
			for imp in r.invoice_id.tax_line_ids.filtered(lambda p: p.name in dic.keys()):
				dict[imp.name] += imp.amount
			lista.append(dict)
		
		
		
		
		_logger.info('lista')
		_logger.info(lista)
		lista.sort(key=lambda date: datetime.strptime(
			date['Fecha'], "%d/%m/%Y"))
		for item in lista:
			item['Num. de Operación'] = op
			op += 1
		tabla = pd.DataFrame(lista)
		return tabla

	def _excel_file_sale(self, table, name, start, end, mf, table_resumen):
		company = self.env['res.company'].search([], limit=1)
		data2 = BytesIO()
		workbook = xlsxwriter.Workbook(data2, {'in_memory': True})
		merge_format = workbook.add_format({
			'bold': 1,
			'border': 1,
			'align': 'center',
			'valign': 'vcenter',
			'fg_color': 'gray'})
		datos = table
		datos_resumen = table_resumen
		total_1 = 0.00
		total_2 = 0.00
		total_3 = 0.00
		total_4 = 0.00
		total_5 = 0.00
		total_6 = 0.00
		total_7 = 0.00
		range_start = 'Desde: ' + \
			datetime.strptime(start, '%Y-%m-%d').strftime('%d/%m/%Y')
		range_end = 'Hasta: ' + \
			datetime.strptime(end, '%Y-%m-%d').strftime('%d/%m/%Y')
		worksheet2 = workbook.add_worksheet(name)
		worksheet2.set_column('A:A', 20)
		worksheet2.set_column('B:B', 50)
		worksheet2.set_column('C:Z', 20)
		worksheet2.write('A1', company.name)
		worksheet2.write('A2', name)
		worksheet2.write('A3', company.vat)
		worksheet2.write('A4', range_start)
		worksheet2.write('A5', range_end)
		worksheet2.merge_range(
			'N5:R5', 'VENTAS INTERNAS O EXPORTACIONES GRAVADAS', merge_format)
		worksheet2.set_row(5, 20, merge_format)
		columnas = list(datos.columns.values)
		columnas_resumen = list(datos_resumen.columns.values)
		columns2 = [{'header': r} for r in columnas]
		columns2_resumen = [{'header': r} for r in columnas_resumen]
		columns2[0].update({'total_string': 'Total'})
		data = datos.values.tolist()
		data_resumen = datos_resumen.values.tolist()
		currency_format = workbook.add_format({'num_format': '#,###0.00'})
		porcent_format = workbook.add_format({'num_format': '#,###0.00" "%'})
		date_format = workbook.add_format()
		date_format.set_num_format('d-mmm-yy')  # Format string.
		col3 = len(columns2) - 1
		col2 = len(data) + 6
		if mf == 'not_installed':
			for record in columns2[10:14]:
				record.update({'format': currency_format})
			for record in columns2[15:16]:
				record.update({'format': currency_format})
			for record in columns2[17:18]:
				record.update({'format': currency_format})
			for record in columns2[19:20]:
				record.update({'format': currency_format})
			for record in columns2[14:15]:
				record.update({'format': porcent_format})
			for record in columns2[16:17]:
				record.update({'format': porcent_format})
			i = 0
			while i < len(data):
				total_1 += data[i][10]
				total_2 += data[i][11]
				total_3 += data[i][12]
				total_4 += data[i][13]
				total_5 += data[i][15]
				total_6 += data[i][17]
				total_7 += data[i][19]
				i += 1

			worksheet2.write_number(col2, 10, float(total_1), currency_format)
			worksheet2.write_number(col2, 11, float(total_2), currency_format)
			worksheet2.write_number(col2, 12, float(total_3), currency_format)
			worksheet2.write_number(col2, 13, float(total_4), currency_format)
			worksheet2.write_number(col2, 15, float(total_5), currency_format)
			worksheet2.write_number(col2, 17, float(total_6), currency_format)
			worksheet2.write_number(col2, 19, float(total_7), currency_format)
		else:
			for record in columns2[12:16]:
				record.update({'format': currency_format})
			for record in columns2[17:18]:
				record.update({'format': currency_format})
			for record in columns2[19:20]:
				record.update({'format': currency_format})
			for record in columns2[11:22]:
				record.update({'format': currency_format})
			for record in columns2[15:16]:#16:17
				record.update({'format': porcent_format})
			for record in columns2[17:18]:#18:19
				record.update({'format': porcent_format})

			i = 0
			while i < len(data):
				total_1 += data[i][11]#12
				total_2 += data[i][12]#13
				total_3 += data[i][13]#14
				total_4 += data[i][14]#15
				total_5 += data[i][16]#17
				total_6 += data[i][18]#19
				total_7 += data[i][20]#21
				i += 1

			worksheet2.write_number(col2, 11, float(total_1), currency_format)#igual a anterior
			worksheet2.write_number(col2, 12, float(total_2), currency_format)
			worksheet2.write_number(col2, 13, float(total_3), currency_format)
			worksheet2.write_number(col2, 14, float(total_4), currency_format)
			worksheet2.write_number(col2, 16, float(total_5), currency_format)
			worksheet2.write_number(col2, 18, float(total_6), currency_format)
			worksheet2.write_number(col2, 20, float(total_7), currency_format)
		cells = xlsxwriter.utility.xl_range(5, 0, col2, col3)
		worksheet2.add_table(
			cells, {'data': data, 'total_row': True, 'columns': columns2})
		encabezado = 4 + len(data) + 6
		detalle_enc = encabezado + 1
		col6 = detalle_enc
		col4 = len(columnas_resumen) - 1
		col5 = len(data) + 6 + 6 + len(data_resumen)
		for record in columns2_resumen[2:8]:
			record.update({'format': currency_format})
		cells_resumen = xlsxwriter.utility.xl_range(col6, 0, col5, col4)
		worksheet2.add_table(
			cells_resumen, {'data': data_resumen, 'total_row': True, 'columns': columns2_resumen, 'header_row': False})
		worksheet2.merge_range(str('A')+str(encabezado)+':'+str('B')+str(encabezado), 'Resumen', merge_format)
		worksheet2.merge_range(str('C') + str(encabezado) + ':' + str('D') + str(encabezado), 'Facturas / Notas de Débito', merge_format)
		worksheet2.merge_range(str('E') + str(encabezado) + ':' + str('F') + str(encabezado), 'Notas de Crédito', merge_format)
		worksheet2.merge_range(str('G') + str(encabezado) + ':' + str('H') + str(encabezado), 'Total Neto', merge_format)

		worksheet2.write(str('A') + str(detalle_enc), '', merge_format)
		worksheet2.write(str('B') + str(detalle_enc), 'Débitos Fiscales',
							   merge_format)
		worksheet2.write(str('C') + str(detalle_enc), 'Base Imponible',
							   merge_format)
		worksheet2.write(str('D') + str(detalle_enc), 'Débito Fiscal', merge_format)
		worksheet2.write(str('E') + str(detalle_enc), 'Base Imponible', merge_format)
		worksheet2.write(str('F') + str(detalle_enc), 'Débito Fiscal',
							   merge_format)
		worksheet2.write(str('G') + str(detalle_enc), 'Base Imponible',
							   merge_format)
		worksheet2.write(str('H') + str(detalle_enc), 'Débito Fiscal', merge_format)
		workbook.close()
		data2 = data2.getvalue()
		return data2

	def _table_sale_book(self, wizard=False):
		if wizard:
			wiz = self.search([('id', '=', wizard)])
		else:
			wiz = self
		tabla1 = wiz._sale_book_invoice_excel()
		union = pd.concat([tabla1])
		return union

	def imprimir_excel(self):
		report = int(self.report)
		filecontent = ''
		report_obj = request.env['wizard.accounting.reports']
		if report == 1:
			table = report_obj._table_shopping_book(self.id)
			name = 'Libro de Compras'
			start = str(self.date_start)
			end = str(self.date_end)
			table_resumen = report_obj._table_resumen_shopping_book(self.id)
		if report == 2:
			table = report_obj._table_sale_book(self.id)
			name = 'Libro de Ventas'
			start = str(self.date_start)
			end = str(self.date_end)
			mf = 'installed' if self.module_mf else 'not_installed'
			table_resumen = report_obj._table_resumen_sale_book(self.id)
		if not table.empty and name:
			if report == 1:
				filecontent = report_obj._excel_file_purchase(
					table, name, start, end, table_resumen)
			if report == 2:
				filecontent = report_obj._excel_file_sale(
					table, name, start, end, mf, table_resumen)
		if not filecontent:
			print("\nAAAAAAAAAAAAAA\n")
			raise exceptions.Warning('No hay datos para mostrar en reporte')
		if report == 1:
			return {
				'type': 'ir.actions.act_url',
				'url': '/web/get_excel?report=%s&wizard=%s&start=%s&end=%s' % (
					self.report, self.id, str(self.date_start), str(self.date_end)),
				'target': 'self'
			}
		if report == 2:
			return {
				'type': 'ir.actions.act_url',
				'url': '/web/get_excel?report=%s&wizard=%s&start=%s&end=%s&mf=%s' % (
					self.report, self.id, str(self.date_start), str(self.date_end), mf),
				'target': 'self'
			}


class AccountingReportsControllerCountry(http.Controller):

	@http.route('/web/get_excel', type='http', auth="user")
	@serialize_exception
	def download_document(self, report, wizard, start, end, mf=None):
		report = int(report)
		filecontent = ''
		if report in [1, 2, 3]:
			report_obj = request.env['wizard.accounting.reports']
		elif report in [4,8]:
			report_obj = request.env['wizard.retention.iva']
		else:
			report_obj = request.env['wizard.retention.islr']
		if report == 1:
			table = report_obj._table_shopping_book(int(wizard))
			name = 'Libro de Compras'
			start = start
			end = end
			table_resumen = report_obj._table_resumen_shopping_book(int(wizard))
		if report == 2:
			table = report_obj._table_sale_book(int(wizard))
			name = 'Libro de Ventas'
			table_resumen = report_obj._table_resumen_sale_book(int(wizard))
		if report == 3:
			raise exceptions.Warning('Reporte no establecido')
		if report == 4:
			table = report_obj._table_retention_iva(int(wizard))
			name = 'Excel Retencion de IVA'
		if report == 8:
			print("GENERAR EL TXT")
			table,lista = report_obj._table_retention_iva_txt(int(wizard))
			name = 'TXT Retencion de IVA'
			f = StringIO()
			for l in lista:
				f.write(l.get('RIF del agente de retención')+"\t")
				f.write(l.get('Período impositivo')+"\t")
				f.write(l.get('Fecha de factura')+"\t")
				f.write(l.get('Tipo de operación')+"\t")
				f.write(l.get('Tipo de documento')+"\t")
				f.write(l.get('RIF de proveedor')+"\t")
				f.write(str(l.get('Número de documento'))+"\t")
				f.write(l.get('Número de control')+"\t")
				f.write(str("{:.2f}".format(l.get('Monto total del documento')))+"\t")
				f.write(str("{:.2f}".format(l.get('Base imponible')))+"\t")
				f.write(str("{:.2f}".format(l.get('Monto del Iva Retenido')))+"\t")
				f.write(str(l.get('Número del documento afectado'))+"\t")
				f.write(str(l.get('Número de comprobante de retención'))+"\t")
				f.write(str("{:.2f}".format(l.get('Monto exento del IVA')))+"\t")
				f.write(str("{:.2f}".format(l.get('Alícuota')))+"\t")
				f.write(l.get('Número de Expediente'))
				f.write("\n")
			f.flush()
			f.seek(0)
			return request.make_response(f, [('Content-Type','text/plain'),('Content-Disposition','attachment; filename=retenciones_iva.txt')])

		if report == 5:
			table = report_obj._table_retention_iva(int(wizard))
			name = 'XML Retencion de ISLR'
		if not table.empty and name:
			if report == 1:
				filecontent = report_obj._excel_file_purchase(
					table, name, start, end, table_resumen)
			if report == 2:
				filecontent = report_obj._excel_file_sale(
					table, name, start, end, mf, table_resumen)
			if report == 4:
				filecontent = report_obj._excel_file_retention(
					table, name, start, end)
			if report == 5:
				filecontent = report_obj._excel_file_retention_islr(
					table, name, start, end)
		if not filecontent:
			print("\nAAAAAAAAAAAAAA\n")
			report_obj.imprimir_excel(int(wizard))
			return
			#return request.not_found()
		print("\Book Sale Country\n")
		#format = report_obj.download_format()
		#format = ".xlsx"
		if report == 5:
			format = '.xlsm'
		else:
			format = '.xlsx'
		return request.make_response(filecontent,
									 [('Content-Type', 'application/pdf'), ('Content-Length', len(filecontent)),
									  ('Content-Disposition', content_disposition(name+format))])
