# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, pycompat, date_utils
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import re
import uuid
import json
from odoo.addons.binaural_mf_backend.models.utils_print import *


class AccountMoveBinauralMFBackend(models.Model):
	_inherit = 'account.move'

	serial_machine = fields.Char(string='Serial de máquina fiscal',copy=False)
	is_credit = fields.Boolean(string='A Crédito')
	machine_invoice_number = fields.Char(string='Numero de factura de maquina',copy=False)
	
	origin_country = fields.Char(string='Origen Country')
	origin_date = fields.Char(string='Fecha origen')

	def has_print_pending(self):
		if not self:
			return False
		if not self.is_sale_document(include_receipts=False):
			return False
		print_pending = self.env['account.move'].search(
			[('state', 'not in', ['draft', 'cancel']), ('serial_machine', '=', False), ('move_type', '=', self.move_type)], limit=1)
		print(self.id)
		print(print_pending.id)
		if print_pending and print_pending.id == self.id:
			print_pending = False
		return print_pending


	#@api.multi
	def action_post(self):
		#tomado de factura contingencia
		# lots of duplicate calls to action_invoice_open, so we remove those already open
		to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
		print_pending = self.has_print_pending()
		#prevent validate invoice if has pending print 
		if print_pending:
			raise UserError(
				"No se puede validar la factura, tiene pendiente por imprimir la factura: "+print_pending.name)

		success = super(AccountMoveBinauralMFBackend, self).action_post()
		if self.move_type in ['out_invoice','out_refund']:
			ref = "ACC."+str(self.partner_id.action_number.number)
			if self.move_type == 'out_invoice':
				sequence = sequence = self._get_sequence()
				new= self.journal_id.sequence_number_next#sequence.get_next_char(sequence.sequence_number_next)
				ref += 'FACT.'+str(self.name)
			if self.move_type == 'out_refund':
				sequence = sequence = self._get_sequence()
				new= 'NC.'+str(self.name) #sequence.get_next_char(sequence.sequence_number_next)
			self.write({"ref":ref})
		return success

	@api.onchange('is_credit')
	def _onchange_is_credit(self):
		for i in self:
			if i.serial_machine:
				raise UserError("No puedes editar una factura impresa")
			if i.is_credit:
				if i.amount_residual != i.amount_total:
					self.is_credit = False
					raise UserError("No puedes convertir una factura a credito si tiene pagos asociados")
					
	#Imprimir Factura De Cliente
	def print_invoice(self):
		#Primero validar que la factura este pagada o al menos que sea a credito
		if self.state in ['draft','cancel']:
			raise UserError("No se puede imprimir una factura sin validar")
		if self.amount_residual != 0 and not self.is_credit:
			raise UserError("No se puede imprimir una factura sin pagar")
		
		if self.is_credit and self.amount_residual != self.amount_total:
			raise UserError(
				"No puedes imprimir una factura a crédito con pagos asociados")

		machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
			[('active', '=', True)], limit=1)
		if machine_info:
			utils_print2 = utils_print(
				machine_info.local, machine_info.host, machine_info.port)
			
			success_last_invoice, number = utils_print2.get_last_invoice_number("FAC")
			if not success_last_invoice:
				
				raise UserError("Error consultando ultima factura " + str(number))
				#chequear que el ultmo + 1 coincida con el numero de la factura que vendra
	
			success,msg = utils_print2.print_customer_invoice(self)
			if success:
				success_last_invoice_after, number_after = utils_print2.get_last_invoice_number("FAC")
				print("success_last_invoice_after", success_last_invoice_after)
				if success_last_invoice_after and number >= number_after:#not success last?
					raise UserError("La secuencia de factura no se incremento")
				else:
					print("la factura actual debe ser la numero"+str(number_after))
					self.write({"serial_machine": machine_info.machine_serial,
								"machine_invoice_number": number_after})
					print("factura impresa, mandar a seguir workflow")
					return False
			else:
				raise UserError(msg)
		else:
			raise UserError("No hay máquina fiscal configurada " + str(machine_info))


	#Imprimir Nota de Credito
	def print_credit_note(self):
		#Primero validar que la factura este pagada o al menos que sea a credito
		if self.state in ['draft', 'cancel']:
			raise UserError("No se puede imprimir una nota sin validar")
		#if self.residual != 0 and not self.is_credit:
			#raise UserError("No se puede imprimir una factura sin pagar")

		#if len(self._get_payments_vals()) > 0 and self.is_credit:
			#raise UserError(
			#    "No puedes imprimir una factura a crédito con pagos asociados")

		machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
			[('active', '=', True)], limit=1)
		if machine_info:
			utils_print2 = utils_print(
				machine_info.local, machine_info.host, machine_info.port)
			success_last_invoice, number = utils_print2.get_last_invoice_number("NC")
			if not success_last_invoice:
				print("number", number)
				raise UserError("Error consultando ultima Nota de credito")
			
			success, msg = utils_print2.print_customer_credit_note(
				self, machine_info)
			if success:
				success_last_invoice_after, number_after = utils_print2.get_last_invoice_number("NC")
				print("success_last_invoice_after", success_last_invoice_after)
				if success_last_invoice_after and number >= number_after:
					raise UserError("La secuencia de nota no se incremento")
				else:
					print("la factura actual debe ser la numero"+str(number))
					self.write({"serial_machine": machine_info.machine_serial,
								"machine_invoice_number": number_after})
					print("factura impresa, mandar a seguir workflow")
			else:
				raise UserError(msg)
		else:
			raise UserError("No hay máquina fiscal configurada")


	def reprint_invoice(self):
		#Primero validar que la factura este impresa
		if not self.serial_machine:
			raise UserError("No puedes reimprimir una factura que no tiene maquina asociada")

		if self.state in ['draft', 'cancel']:
			raise UserError("No se puede imprimir una factura sin validar")

		machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
			[('active', '=', True)], limit=1)
		if machine_info:
			utils_print2 = utils_print(
				machine_info.local, machine_info.host, machine_info.port)
			success, msg = utils_print2.reprint_customer_invoice(self)
			if success:
				#self.write({"serial_machine": machine_info.machine_serial})
				print("factura reimpresa, mandar a seguir workflow")
			else:
				raise UserError(msg)
		else:
			raise UserError("No hay máquina fiscal configurada")


	def get_data_programed(self):
		machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
			[('active', '=', True)], limit=1)
		if machine_info:
			utils_print2 = utils_print(
				machine_info.local, machine_info.host, machine_info.port)
			success, msg = utils_print2.print_programed()
			if success:
				print("Programación impresa")
			else:
				raise UserError(msg)
		else:
			raise UserError("No hay máquina fiscal configurada")

	def get_status(self):
		machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
			[('active', '=', True)], limit=1)
		if machine_info:
			utils_print2 = utils_print(
				machine_info.local, machine_info.host, machine_info.port)
			success, msg = utils_print2.obtener_estado_maquina("S1")
			if success:
				raise UserError(msg)
			else:
				raise UserError(msg)
		else:
			raise UserError("No hay máquina fiscal configurada")

	def get_status_error(self):
		machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
			[('active', '=', True)], limit=1)
		if machine_info:
			utils_print2 = utils_print(
				machine_info.local, machine_info.host, machine_info.port)
			print("----")
			success, msg = utils_print2.obtener_estado_error()
			if success:
				raise UserError(msg)
			else:
				raise UserError(msg)
		else:
			raise UserError("No hay máquina fiscal configurada")

	def get_last_invoice_number(self,type_doc):
		machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
			[('active', '=', True)], limit=1)
		if machine_info:
			utils_print2 = utils_print(
				machine_info.local, machine_info.host, machine_info.port)
			success, msg = utils_print2.get_last_invoice_number(type_doc)
			if success:
				return msg
			else:
				raise UserError(msg)
		else:
			raise UserError("No hay máquina fiscal configurada")
