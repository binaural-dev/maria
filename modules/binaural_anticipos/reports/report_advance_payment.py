# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo import api, fields, exceptions, http, models, _

class ReportMemberList2(models.AbstractModel):
	_name = 'report.binaural_anticipos.advance_payment_template_report'

	@api.model
	def _get_report_values(self, docids, data=None):
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
		print("data context",data.get('context'))
		ctx = data.get('context',False)
		name_user = ''
		if ctx:
			uid = ctx.get('uid')
			obj_uid = self.env['res.users'].sudo().search([('id','=',uid)])
			if obj_uid:
				name_user = obj_uid.name
		form = data.get('form',False)
		if not form:
			raise UserError("Error en formulario de reporte")
		print("form",form)
		docs = self.env['wizard.advance.payment.list'].browse(self.env.context.get('active_id'))

		type_report = form.get('type_report',False)
		type_payment = form.get('type_payment',False)
		all_partner = form.get('all_partner',False)
		partner = form.get('partner',False)
		at_today = form.get('at_today',False)
		start_date = form.get('start_date',False)
		end_date = form.get('end_date',False)
		type_residual = form.get('type_residual',False) 

		search_domain = []
		domain = []
		name_report = 'Listado de anticipos'
		if type_payment == 'advance':
			if type_report and type_report == 'supplier':
				#search_domain += [('type','=','outbound')]
				domain += [('supplier_rank','>',0)]
				name_report = 'Listado de anticipos de proveedores'
			else:
				#search_domain += [('type','=','inbound')]
				domain += [('customer_rank','>',0)]
				name_report = 'Listado de anticipos de clientes'
		else:
			if type_report and type_report == 'supplier':
				#search_domain += [('type','=','outbound')]
				domain += [('supplier_rank','>',0)]
				name_report = 'Listado de pagos de proveedores'
			else:
				#search_domain += [('type','=','inbound')]
				domain += [('customer_rank','>',0)]
				name_report = 'Listado de pagos de clientes'

		client_ids = []
		
		
		if not all_partner and partner:
			client_ids = self.env['res.partner'].sudo().browse(partner)
		else:
			if type_report and type_report == 'supplier':
				search_domain += [('payment_type','=','outbound')]
			else:
				search_domain += [('payment_type','=','inbound')]

			if type_payment and type_payment == 'advance':
				search_domain += [('is_advance','=',True)]
			elif type_payment and type_payment == 'payment':
				search_domain += [('is_advance','=',False),('is_expense','=',False)]
			elif type_payment and type_payment == 'is_expense':
				search_domain += [('is_expense','=',True)]

			if at_today:
				search_domain += [('date','<=',fields.Date.today())]
			else:
				search_domain += [('date','<=',end_date),('date','>=',start_date)]

			payments = self.env['account.payment'].sudo().search(search_domain)
			if type_residual != 'all':
				print("filtrar por solo los que no tengan saldo")
				new_payments = []
				for p in payments:
					acum = docs.get_residual_by_payment(p)
					if(acum == 0 and type_residual == 'zero') or (acum != 0 and type_residual == 'with'):
						new_payments.append(p)
				payments = new_payments
			#buscar todos los pagos con el criterio del wizard para saber los clientes que debo buscar
			for p in payments:
				if p.partner_id not in client_ids:
					client_ids.append(p.partner_id)
			#client_ids = self.env['res.partner'].sudo().search(domain) #buscos todos los clientes
		print("client_ids",client_ids)


		return {
			'data': data['form'],
			'docs': docs,
			'client_ids':client_ids,
			'date':date.today(),
			'name_user':name_user,
			'name_report':name_report,
		}


