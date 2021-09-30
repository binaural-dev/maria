# -*- coding: utf-8 -*-

from odoo import api, fields, exceptions, http, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import xlsxwriter

from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception,content_disposition
from io import BytesIO
import logging
import time

from collections import OrderedDict
import pandas as pd
import sys

import os

_logger = logging.getLogger(__name__)

dict_month = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril',5:'Mayo',6:'Junio', 7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre',11:'Noviembre',12:'Diciembre'}
month_names = ['Enero - Bs','Febrero - Bs','Marzo - Bs','Abril - Bs','Mayo - Bs','Junio - Bs','Julio - Bs','Agosto - Bs','Septiembre - Bs','Octubre - Bs','Noviembre - Bs','Diciembre - Bs','Enero - USD','Febrero - USD','Marzo - USD','Abril - USD','Mayo - USD','Junio - USD','Julio - USD','Agosto - USD','Septiembre - USD','Octubre - USD','Noviembre - USD','Diciembre - USD']
class CuentaPorCobrarCountryClub(models.TransientModel):
	_name = "country.account.to.pay"
	
	at_today  = fields.Boolean(string='A la fecha actual',default=False)

	start_date  = fields.Date(string='Desde',default=date.today().replace(day=1))

	end_date  = fields.Date(string='Hasta',default=date.today().replace(day=1)+relativedelta(months=1, days=-1))


	
	def _account_receivable_country(self, wizard=False):
		month = ''
		if wizard:
			wiz = self.search([('id', '=', wizard)])
		else:
			wiz = self
		
		titulo = "Cuentas por Cobrar"

		search_domain = [('active', '=', True),('parent_id','=',False),('customer','=',True),('supplier','=',False),('action_number','!=',False)]
		docs = self.env['res.partner'].sudo().search(search_domain)

		dic = OrderedDict([
			('Nro',''),
			('Tipo de Acción', ''),
			('Nro de Acción', ''),
			('Estado del socio', ''),
			('Nombre y Apellido', ''),
			
		])
				
		search_domain = [('state','not in',['draft','cancelled'])]
		search_domain += [('payment_type','=','inbound')]
		search_domain += [('payment_date','<=',wiz.end_date),('payment_date','>=',wiz.start_date)]
		payments = self.env['account.payment'].sudo().search(search_domain)
		#determinar meses en las columnas: periodos pagados con pagos de este mes
		
		months = []
		for p in payments:
			for i in p.invoice_ids:
				if i.state in ['paid','in_payment','open']:
					#print("el pago en el rango elegido tiene una factura asociada del periodo:",i.fee_period)
					if i.fee_period and (i.fee_period.month,i.fee_period.year) not in months:
						months.append((i.fee_period.month,i.fee_period.year))
		
		print("months",months)
		#months.sort(reverse=True)
		fechas = []
		for l in months:
			date = datetime.strptime('01'+str(l[0])+str(l[1]), "%d%m%Y").date()
			print("FECHAAAAAAAAA",date)
			fechas.append(date)

		fechas.sort(reverse=True)
		print("fechas ordenadassssssss",fechas)



		for m in fechas:
			mn = dict_month[m.month]
			dic[mn+' '+str(m.year)+' - USD'] = ''
			dic[mn+' '+str(m.year)+' - Bs'] = ''
			
		#result = []

		lista = []
		total_base = 0
		nro_op = 0

		for i in docs:
			total_bs = 0
			total_usd = 0
			total_advance = 0
			dicti = OrderedDict()
			dicti.update(dic)
			#total_base += i.residual_signed
			
			type_action_dict = {'action':'Acción','extention':'Extensión'}
			state_partner_dict = {'active':'Activo','holder':'Tenedor','deceased':'Fallecido','inactive':'Inactivo'}

			dicti['Tipo de Acción'] = str(type_action_dict[i.type_of_member])
			dicti['Estado del socio'] = str(state_partner_dict[i.state_partner])
			dicti['Nro de Acción'] = str(i.action_number.number)
			dicti['Nombre y Apellido'] = i.name.capitalize()

			for m in fechas:
				mn = dict_month[m.month]
				bs,usd,advance = wiz.amount_payment_in_month(m,i,payments)
				total_bs += bs
				total_usd += usd
				total_advance += advance
				dicti[mn+' '+str(m.year)+' - Bs'] = bs
				dicti[mn+' '+str(m.year)+' - USD'] = usd
			dicti['Total USD'] = total_usd
			dicti['Total Bs'] = total_bs
			dicti['Anticipo'] = total_advance
			lista.append(dicti)
		if len(lista) > 0:
			lista.sort(key=lambda d: d['Nro de Acción'])
			for item in lista:
				nro_op += 1
				item['Nro'] = nro_op
			tabla = pd.DataFrame(lista)#.sort_values(['Nro de Acción'], ascending=[1])
			return tabla,total_base,wiz,nro_op
		else:
			tabla = pd.DataFrame(lista)
			return tabla,total_base,wiz,nro_op

	def _excel_file_country_club_cuentas_por_cobrar(self,tabla,nombre,total_base,wiz,nro_op):

		data2 = BytesIO()
		date = 'Fecha: ' + str(time.strftime("%d/%m/%y"))
		workbook = xlsxwriter.Workbook(data2, {'in_memory': True})
		datos = tabla
		general = workbook.add_format()
		general.set_text_wrap()
		general.set_align('center')
		general.set_align('vcenter')
		nombre = 'Cuenta por cobrar'
		worksheet2 = workbook.add_worksheet(nombre)
		worksheet2.set_default_row(24)

		worksheet2.set_column('A:Z', 24)

		columnas = list(datos.columns.values)
		columns2 = [{'header':r} for r in columnas]
		currency_format = workbook.add_format({'num_format': '#,##0.00'})

		data = datos.values.tolist()
		last_column = len(columns2)-1
		last_row = len(data)+1
		header_format = workbook.add_format({'bold': True,
									 'bottom': 2,
									 })#'bg_color': '#7EF7D0'
		header_format.set_align('center')
		header_format.set_align('vcenter')
		header_format.set_border(1)
		header_format.set_locked()
		company_name = self.env.user.company_id.name
		
		for record in columns2[:5]:
			#print(record.get("header"))
			if record.get("header") == 'Nombre y Apellido':
				record.update({'format': general})
		for record in columns2[5:]:
			record.update({'format': currency_format})
		cells = xlsxwriter.utility.xl_range(0,0,last_row+0,last_column+0)


  
		worksheet2.add_table(cells, {'data': data, 'total_row': 1, 'columns':columns2,'header_row': True,'style': 'Table Style Light 11'})

		for col_num, value in enumerate(columnas):
			worksheet2.write(0, col_num , value, header_format)


		workbook.close()
		data2 = data2.getvalue()
		return data2

	def imprimir_excel_cuenta_por_cobrar(self):
		_logger.info(self)
		_logger.info(self.id)
	 
		return {
			'type': 'ir.actions.act_url',
			'url': '/web/get_account_to_pay_country_club?&wizard=%s' % (self.id),
			'target': 'self'
		}

	def amount_payment_in_month(self,m,partner,payments):
		print("monto a buscar para el partner",partner.name)
		print("para el periodo",m)
		#print("arreglo de pagos",payments)
		payments_for_payment = payments.filtered(lambda p: p.partner_id.id == partner.id)
		#print("payments_for_payment",payments_for_payment)
		amount = 0
		amount_usd = 0
		acum_advance = 0
		#si un pago se divide en 2 facturas de periodos diferentes
		for pp in payments_for_payment:
			for i in pp.invoice_ids:
				if i.fee_period and i.fee_period.month == m.month and i.fee_period.year == m.year:
					#amount += pp.amount
					#print("payment_move_line_ids",i.payment_move_line_ids)
					for ip in i.payment_move_line_ids:
						#print("esta linea asociada a factura tiene el pago",ip.payment_id)
						#print("y el pago donde estoy consultando es el pago",pp)
						amount_match = sum([p.amount for p in ip.matched_debit_ids if p.debit_move_id in i.move_id.line_ids])
						#print("amount_match",amount_match)
						if pp.journal_id.name and pp.journal_id.name.find('$') != -1: 
							amount_usd +=amount_match
						else:
							amount +=amount_match
						if pp.is_advance:
							acum_advance += amount_match
						#if ip.payment_id == pp:
						#	print("son igualessssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss",ip.credit)
		print("amount",amount)
		return amount,amount_usd,acum_advance
class wizard_country_club_get_excel_controller(http.Controller):

	@http.route('/web/get_account_to_pay_country_club', type='http', auth="user")
	@serialize_exception
	def download_document(self,wizard,debug=0):
		filecontent = ''
		report_obj = request.env['country.account.to.pay']
		if wizard:
			wiz = report_obj.search([('id', '=', wizard)])
		else:
			wiz = report_obj
	 
		#print("llamar a objeto y excel mercantil")
		nombre = 'CuentaPorCobrarCountrYClubBqto'
		format = '.xlsx'
		tabla,total_base,wiz,nro_op = report_obj._account_receivable_country(int(wizard))
		if not tabla.empty and nombre:
			filecontent = report_obj._excel_file_country_club_cuentas_por_cobrar(tabla,nombre,total_base,wiz,nro_op)

		return request.make_response(filecontent,
		[('Content-Type', 'application/pdf'), ('Content-Length', len(filecontent)),
		('Content-Disposition', content_disposition(nombre+format))])