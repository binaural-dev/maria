# -*- coding: utf-8 -*-

from collections import OrderedDict
import json
import re
import uuid
from functools import partial

from lxml import etree
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode

from odoo import api, exceptions, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
	pycompat, date_utils
from odoo.tools.misc import formatLang

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

from odoo.addons import decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)

class account_payment_inh(models.Model):
	_inherit = 'account.invoice'
	outstanding_credits_debits_widget2 = fields.Text(compute='_get_outstanding_info_JSON2', groups="account.group_account_invoice")

	@api.one
	def _get_outstanding_info_JSON2(self):
		self.outstanding_credits_debits_widget2 = json.dumps(False)		
		if self.state == 'open':
			domain = [('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
					  ('reconciled', '=', False),
					  ('move_id.state', '=', 'posted'),
					  '|',
						'&', ('amount_residual_currency', '!=', 0.0), ('currency_id','!=', None),
						'&', ('amount_residual_currency', '=', 0.0), '&', ('currency_id','=', None), ('amount_residual', '!=', 0.0)]
			if self.type in ('out_invoice', 'in_refund'):
				print("es creditos")
				advance_account = self.env['account.payment.config.advance'].search([('active','=',True),('advance_type','=','customer')],limit=1)
				if advance_account:
					domain.extend([('account_id', '=', advance_account.advance_account_id.id)])
				domain.extend([('credit', '>', 0), ('debit', '=', 0)])
				
				type_payment = _('Anticipos')
			else:
				print("es debitos")
				advance_account = self.env['account.payment.config.advance'].search([('active','=',True),('advance_type','=','supplier')],limit=1)
				if advance_account:
					domain.extend([('account_id', '=', advance_account.advance_account_id.id)])
				domain.extend([('credit', '=', 0), ('debit', '>', 0)])
				type_payment = _('Anticipos')
			info = {'title': '', 'outstanding': True, 'content': [], 'invoice_id': self.id}
			if advance_account:
				lines = self.env['account.move.line'].search(domain)
			else:
				lines = []
			currency_id = self.currency_id
			if len(lines) != 0:
				for line in lines:
					# get the outstanding residual value in invoice currency
					if line.currency_id and line.currency_id == self.currency_id:
						amount_to_show = abs(line.amount_residual_currency)
					else:
						currency = line.company_id.currency_id
						amount_to_show = currency._convert(abs(line.amount_residual), self.currency_id, self.company_id, line.date or fields.Date.today())
					if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
						continue
					if line.ref :
						title = '%s : %s' % (line.move_id.name, line.ref)
					else:
						title = line.move_id.name
					info['content'].append({
						'journal_name': line.ref or line.move_id.name,
						'title': title,
						'amount': amount_to_show,
						'currency': currency_id.symbol,
						'id': line.id,
						'position': currency_id.position,
						'digits': [69, self.currency_id.decimal_places],
					})
				info['title'] = type_payment
				self.outstanding_credits_debits_widget2 = json.dumps(info)
				self.has_outstanding = True
	@api.multi
	def register_payment(self, payment_line, writeoff_acc_id=False, writeoff_journal_id=False):
		""" Reconcile payable/receivable lines from the invoice with payment_line """
		line_to_reconcile = self.env['account.move.line']
		for inv in self:
			line_to_reconcile += inv._get_aml_for_register_payment()

		if payment_line.payment_id.is_advance:
			move = self.make_entry_advance_reconcile(payment_line)

			if move:
				for line in move.line_ids:
					if line.account_id == payment_line.account_id:
						payment_line_two = line
						break
				if payment_line_two:
					#conciliar el anticipo y la linea del monto usado en el puente
					concilie_advance = (payment_line + payment_line_two).reconcile(False, False)

				#change default payment_line to generate in bridge move
				for l in move.line_ids:
					if l.account_id == line_to_reconcile.account_id:
						payment_line = l
						break
		#conciliar factura con el monto de la linea del asiento puente
		return (line_to_reconcile + payment_line).reconcile(writeoff_acc_id, writeoff_journal_id)

	def make_entry_advance_reconcile(self,payment_line):

		if self.type not in ('out_invoice', 'in_refund'):
			advance_account = self.env['account.payment.config.advance'].search([('active','=',True),('advance_type','=','supplier')],limit=1)		
			if not advance_account:
				raise UserError("Cuenta contable de anticipo no configurada")
			if payment_line.currency_id and payment_line.currency_id == self.currency_id:
				amount = abs(payment_line.amount_residual_currency)
				amount = self.currency_id.round(amount)
			else:
				currency = payment_line.company_id.currency_id
				amount = currency._convert(abs(payment_line.amount_residual), self.currency_id,
				                           self.company_id, payment_line.date or fields.Date.today())
				amount = currency.round(amount)
			line_ret = [(0, 0, {
				#tomar esta linea para reconciliar
				'name': 'CUENTA POR PAGAR PROVEEDOR',
				'account_id': self.account_id.id,#cuenta de la factura, CXP
				'partner_id': self.partner_id.id,
				'debit': amount,
				'credit': 0,
				'payment_id_advance': payment_line.payment_id.id,
			}), (0, 0, {
				'name': 'ANTICIPO/PROVEEDOR',
				'account_id': advance_account.advance_account_id.id,#Cuenta de anticipo configurada
				'partner_id': self.partner_id.id,
				'debit': 0,
				'credit': amount,
				'payment_id_advance': payment_line.payment_id.id,
			})]
			move_obj = self.env['account.move'].create({
				'name': self.number,
				'date': fields.Date.today(),
				'journal_id': self.journal_id.id if self.journal_id else 1,
				'state': 'posted',
				'line_ids': line_ret,
				'company_id':self.company_id.id,
			})
			return move_obj
		else:
			advance_account = self.env['account.payment.config.advance'].search([('active','=',True),('advance_type','=','customer')],limit=1)		
			if not advance_account:
				raise UserError("Cuenta contable de anticipo no configurada")
			if payment_line.currency_id and payment_line.currency_id == self.currency_id:
				amount = abs(payment_line.amount_residual_currency)
				amount = self.currency_id.round(amount)
			else:
				currency = payment_line.company_id.currency_id
				amount = currency._convert(abs(payment_line.amount_residual), self.currency_id,
				                           self.company_id, payment_line.date or fields.Date.today())
				amount = currency.round(amount)
			
			line_ret = [(0, 0, {
				#tomar esta linea para reconciliar
				'name': 'CUENTA POR COBRAR CLIENTE',
				'account_id': self.account_id.id,#cuenta de la factura, CXC
				'partner_id': self.partner_id.id,
				'credit': amount,
				'debit': 0,
				'payment_id_advance':payment_line.payment_id.id,
			}), (0, 0, {
				'name': 'ANTICIPO/CLIENTE',
				'account_id': advance_account.advance_account_id.id,#anticipo
				'partner_id': self.partner_id.id,
				'debit': amount,
				'credit': 0,
				'payment_id_advance': payment_line.payment_id.id,
			})]
			move_obj = self.env['account.move'].create({
				'name': self.number,
				'date': fields.Date.today(),
				'journal_id': self.journal_id.id if self.journal_id else 1,
				'state': 'posted',
				'line_ids': line_ret,
				'company_id':self.company_id.id,
			})
			return move_obj

