from odoo.addons.binaural_mf_backend.sdk_tfhka.Tfhka import Tfhka
from datetime import (timedelta, datetime as pyDateTime,
					  date as pyDate, time as pyTime)

import sys

import serial
import os
import time
from datetime import (timedelta, datetime as pyDateTime, date as pyDate, time as pyTime)
from odoo import api, fields, SUPERUSER_ID
import sys
import unicodedata
import logging
_logger = logging.getLogger(__name__)
class utils_print():

	def __init__(self, tipo_conexion=True, host='', port=''):
		self.printer = Tfhka(tipo_conexion,host,port)  # Tfhka.Tfhka()

	def obtener_estado_maquina(self,estado):
		try:
			if not estado:
				return False, "Estado es obligatorio"

			self.cerrar_puerto()
			time.sleep(2)
			success_port, msg = self.abrir_puerto()
			time.sleep(1)
			if success_port:
				state, error = self.estado_error()
				if state == "4" and error in ["0","1"]:
					printed, invoice_msg = self.obtener_estado(estado)
					time.sleep(2)
					self.cerrar_puerto()
					return printed, invoice_msg
				else:
					return False, error
			else:
				print("puerto no conectado o no existe factura")
				return False, msg
		except Exception as e:
			print("exepcion", str(e))
			return False, str(e)

	def obtener_estado_error(self):
		try:
			self.cerrar_puerto()
			time.sleep(2)
			success_port, msg = self.abrir_puerto()
			time.sleep(1)
			if success_port:
				s,state = self.estado_error_completo()
				time.sleep(2)
				self.cerrar_puerto()
				return True,state
			else:
				print("puerto no conectado o no existe factura")
				return False, msg
		except Exception as e:
			print("exepcion", str(e))
			return False, str(e)
	def reprint_customer_invoice(self, invoice):
		try:
			if not invoice:
				return False, "Factura es obligatoria"

			self.cerrar_puerto()
			time.sleep(2)
			success_port, msg = self.abrir_puerto()
			print("abrir puerto", msg)
			time.sleep(1)
			if success_port:
				state, error = self.estado_error()
				print("Estado", state)
				print("error", error)
				if state in ["4", "5"] and error in ["0", "1"]:  # temporal
					printed, invoice_msg = self.reprint_invoice_bin(invoice)
					time.sleep(2)
					self.cerrar_puerto()
					return printed, invoice_msg
				else:
					return False, "El estado de la maquina no es valido"
			else:
				print("puerto no conectado o no existe factura")
				return False, msg
		except Exception as e:
			print("exepcion", str(e))
			return False, str(e)
	def print_customer_invoice(self,invoice):
		try:
			if not invoice:
				return False,"Factura es obligatoria"

			self.cerrar_puerto()
			time.sleep(2)
			success_port, msg = self.abrir_puerto()
			print("abrir puerto",msg)
			time.sleep(1)
			if success_port:
				state,error = self.estado_error()
				print("Estado",state)
				print("error",error)
				if state in ["4","5"] and error in ["0","1"]:#temporal
					#if 1==1:
					printed,invoice_msg = self.print_invoice_bin(invoice)
					time.sleep(2)
					self.cerrar_puerto()
					return printed, invoice_msg
				else:
					return False,"El estado de la maquina no es valido"
			else:
				print("puerto no conectado o no existe factura")
				return False,msg
		except Exception as e:
			print("exepcion",str(e))
			return False,str(e)

	def print_programed(self):
		try:
			self.cerrar_puerto()
			time.sleep(2)
			success_port, msg = self.abrir_puerto()
			time.sleep(1)
			if success_port:
				state, error = self.estado_error()
				if state == "4" and error in ["0", "1"]:
					printed, invoice_msg = self.programacion()
					time.sleep(2)
					self.cerrar_puerto()
					return printed, invoice_msg
				else:
					return False, error
			else:
				print("puerto no conectado o no existe factura")
				return False, msg
		except Exception as e:
			print("exepcion", str(e))
			return False, str(e)

	
	def abrir_puerto(self):
		try:
			resp = self.printer.OpenFpctrl()
			if resp:
				return True,"Impresora Conectada Correctamente en: "
			else:
				return False,"Impresora no Conectada o Error Accediendo al Puerto"
		except serial.SerialException:
			return False,"Impresora no Conectada o Error Accediendo al Puerto"

	def cerrar_puerto(self):
		resp = self.printer.CloseFpctrl()
		if not resp:
			return True,"Impresora Desconectada"
		else:
			return False,"Error"

	def obtener_estado(self,estado):
		if estado == "S1":
			try:
				estado_s1 = self.printer.GetS1PrinterData()
				print(str(estado_s1))
				salida = "---Estado S1---\n"
				salida += "\nNumero Cajero: " + str(estado_s1._cashierNumber)
				salida += "\nSubtotal Ventas: " + str(estado_s1._totalDailySales)
				salida += "\nNumero Ultima Factura: " + str(estado_s1._lastInvoiceNumber)
				salida += "\nCantidad Facturas Hoy: " + \
					str(estado_s1._quantityOfInvoicesToday)
				salida += "\nNumero Ultima Nota de Debito: " + \
					str(estado_s1._lastDebtNoteNumber)
				salida += "\nCantidad Notas de Debito Hoy: " + \
					str(estado_s1._quantityDebtNoteToday)
				salida += "\nNumero Ultima Nota de Credito: " + str(estado_s1._lastNCNumber)
				salida += "\nCantidad Notas de Credito Hoy: " + \
					str(estado_s1._quantityOfNCToday)
				salida += "\nNumero Ultimo Documento No Fiscal: " + \
					str(estado_s1._numberNonFiscalDocuments)
				salida += "\nCantidad de Documentos No Fiscales: " + \
					str(estado_s1._quantityNonFiscalDocuments)
				salida += "\nCantidad de Reportes de Auditoria: " + \
					str(estado_s1._auditReportsCounter)
				salida += "\nCantidad de Reportes Fiscales: " + \
					str(estado_s1._fiscalReportsCounter)
				salida += "\nCantidad de Reportes Z: " + str(estado_s1._dailyClosureCounter)
				salida += "\nNumero de RIF: " + str(estado_s1._rif)
				salida += "\nNumero de Registro: " + str(estado_s1._registeredMachineNumber)
				salida += "\nHora de la Impresora: " + str(estado_s1._currentPrinterTime)
				salida += "\nFecha de la Impresora: " + str(estado_s1._currentPrinterDate)
				return True, salida
				#self.txt_informacion.setText(salida)
			except Exception as e:
				return False,e
				

		if estado == "S2":
			estado_s2 = self.printer.GetS2PrinterData()
			salida = "---Estado S2---\n"
			salida += "\nSubtotal de BI: " + str(estado_s2._subTotalBases)
			salida += "\nSubtotal de Impuesto: " + str(estado_s2._subTotalTax)
			salida += "\nData Dummy: " + str(estado_s2._dataDummy)
			salida += "\nCantidad de articulos: " + str(estado_s2._quantityArticles)
			salida += "\nMonto por Pagar: " + str(estado_s2._amountPayable)
			salida += "\nNumero de Pagos Realizados: " + \
				str(estado_s2._numberPaymentsMade)
			salida += "\nTipo de Documento: " + str(estado_s2._typeDocument)
			#self.txt_informacion.setText(salida)
			return True, salida

		if estado == "S3":
			estado_s3 = self.printer.GetS3PrinterData()
			salida = "---Estado S3---\n"
			salida += "\nTipo Tasa 1 (1 = Incluido, 2= Excluido): " + \
							str(estado_s3._typeTax1)
			salida += "\nValor Tasa 1: " + str(estado_s3._tax1) + " %"
			salida += "\nTipo Tasa 2 (1 = Incluido, 2= Excluido): " + \
							str(estado_s3._typeTax2)
			salida += "\nValor Tasa2: " + str(estado_s3._tax2) + " %"
			salida += "\nTipo Tasa 3 (1 = Incluido, 2= Excluido): " + \
							str(estado_s3._typeTax3)
			salida += "\nValor Tasa 3: " + str(estado_s3._tax3) + " %"
			salida += "\n\nLista de Flags: " + str(estado_s3._systemFlags)
			return True,salida
			#self.txt_informacion.setText(salida)

		if estado == "S4":
			estado_s4 = self.printer.GetS4PrinterData()
			salida = "---Estado S4---\n"
			salida += "\nMontos en Medios de Pago: " + str(estado_s4._allMeansOfPayment)
			#self.txt_informacion.setText(salida)
			return True, salida

		if estado == "S5":
			estado_s5 = self.printer.GetS5PrinterData()
			salida = "---Estado S5---\n"
			salida += "\nNumero de RIF: " + str(estado_s5._rif)
			salida += "\nNumero de Registro: " + str(estado_s5._registeredMachineNumber)
			salida += "\nNumero de Memoria de Auditoria : " + \
				str(estado_s5._auditMemoryNumber)
			salida += "\nCapacidad Total de Memoria Auditoria: " + \
				str(estado_s5._auditMemoryTotalCapacity) + " MB"
			salida += "\nEspacio Disponible: " + \
				str(estado_s5._auditMemoryFreeCapacity) + " MB"
			salida += "\nCantidad Documentos Registrados: " + \
				str(estado_s5._numberRegisteredDocuments)
			self.txt_informacion.setText(salida)

		if estado == "S6":
			estado_s6 = self.printer.GetS6PrinterData()
			salida = "---Estado S6---\n"
			salida += "\nModo Facturacion: " + str(estado_s6._bit_Facturacion)
			salida += "\nModo Slip: " + str(estado_s6._bit_Slip)
			salida += "\nModo Validacion: " + str(estado_s6._bit_Validacion)
			self.txt_informacion.setText(salida)

	def estado_error(self):
		self.estado = self.printer.ReadFpStatus()
		try:
			print("ESTADO BRUTO:",str(self.estado))
			return self.estado[0], self.estado[5]
		except Exception as e:
			print(e)
			return False,False

	def estado_error_completo(self):
		try:
			self.estado = self.printer.ReadFpStatus()
			return True,self.estado
		except Exception as e:
			print(e)
			return False, False
	def reprint_invoice_bin(self,invoice):
		if invoice.machine_invoice_number:
			try:
				#machine number es el numero de la factura a reimpirmir
				machine_number_i = invoice.machine_invoice_number
				machine_number_f = invoice.machine_invoice_number
				#en este caso el inicio y fin es el mismo
				#print("[1:]", machine_number_i[1:])#se toman los 7 ultimos
				if invoice.move_type == "out_invoice":
					mode = "RF"
				if invoice.move_type == "out_refund":
					mode = "RC"
				if not mode:
					return False, "Tipo de documento no valido"
				com = str(mode+str(machine_number_i.zfill(7)+str(machine_number_f.zfill(7))))
				self.printer.SendCmd(com)
				return True, "Documento reimpreso correctamente"
			except Exception as e:
				return False, str(e)
		else:
			return False,"Algo salio mal con los parametros de la factura, verifique la informacion"
		

	def print_invoice_bin(self,invoice):
		#Factura Personalizada
		valid,invoice_data = self.validate_invoice_parameter(invoice)
		if valid and invoice_data:
			try:
				self.printer.SendCmd(str("iR*"+invoice_data.get("vat")))
				self.printer.SendCmd(str("iS*"+invoice_data.get("name")))
				self.printer.SendCmd(str("i00ACCION: "+invoice_data.get("action_number","")))
				self.printer.SendCmd(str("i01TELEFONO: "+invoice_data.get("phone")))
				self.printer.SendCmd(str("i02"+invoice_data.get("company_name", "")))

				for item in invoice_data.get("items", []):
					time.sleep(1)
					self.printer.SendCmd(str("GF+"+item.get("tax")+item.get("price") +"||"+
								item.get("qty")+"||"+item.get("name")+item.get("code")))

				self.printer.SendCmd(str("3"))  # sub total en factura
				#poner todas como parcial
				#for payment in invoice_data.get("payments",[]):
				#	cmd_success = self.printer.SendCmd("2"+str(payment.get("code")+payment.get("amount")))
				#	print("cmd_success", cmd_success)
				#	if not cmd_success:
				#		return False,"Error enviando comando a la maquina"
				#time.sleep(1)
				#amount_due = self.get_amount_to_pay()
				#time.sleep(1)
				#print(amount_due)
				#if amount_due > 0:
				#	self.printer.SendCmd(str("101"))
				self.printer.SendCmd(str("101"))
				

				print("termino de imprimir")
				return True, "Factura impresa correctamente"
			except Exception as e:
				return False, str(e)
		else:
			return False,"Algo salio mal con los parametros de la factura, verifique la informacion"
	#function to remove special char
	def strip_accents(self,text):
		try:
			text = unicode(text, 'utf-8')
		except NameError:  # unicode is a default on python 3
			pass
		
		text = text.encode('ascii')
		print("============")
		print(typeof(text))
		print(text)
		#text = unicodedata.normalize('NFD', text)\
		#	.encode('ascii', 'ignore')\
		#	.decode("utf-8")
		return str(text)




	def validate_invoice_parameter(self,invoice):
		_logger.info("invoice %s",invoice)
		invoice_data = {}
		if not invoice:
			return False,invoice_data
		if invoice.machine_invoice_number or invoice.serial_machine:
			return False,invoice_data		

		if not invoice.partner_id.vat:
			return False,invoice_data
		else:
			invoice_data["vat"] = invoice.vat
		
		if not invoice.partner_id.name:
			return False,invoice_data
		else:
			invoice_data["name"] = invoice.partner_id.name
		
		if not invoice.action_number:
			#return False,invoice_data
			invoice_data["action_number"] = ""
		else:
			invoice_data["action_number"] = invoice.action_number
		
		
		if not invoice.partner_id.phone:
			return False,invoice_data
		else:
			invoice_data["phone"] = invoice.partner_id.phone

		if not invoice.company_id:
			return False,invoice_data
		else:
			invoice_data["company_name"] = invoice.company_id.name
		#recorrer todos los pagos asociados y verificar los diarios (son los medios de pago en la maquina) o anticipo y credito buscar
		payments = []
		if not invoice.is_credit:
			_logger.info("cantidad de pagos asociados a la factura")
			_logger.info(invoice.invoice_payments_widget)
			_logger.info("_get_reconciled_info_JSON_values %s",invoice._get_reconciled_info_JSON_values())
			for pv in invoice._get_reconciled_info_JSON_values():
				payment = {}
				amount = pv.get("amount") * invoice.foreign_currency_rate
				payment["amount"] = str(format(
					invoice.currency_id.round(amount), '.2f')).replace('.', '').zfill(12)
				journal_obj = invoice.env['account.journal'].search([('name','=',pv.get("journal_name"))])
		
				if journal_obj.id_machine_payment:
					code_payment = journal_obj.id_machine_payment
				else:
					is_advance = self._is_advance_payment(pv, invoice)
					if is_advance:
						print("es avance buscar el medio de pago de avance")
						mp = invoice.env['bin_maquina_fiscal_medios_pago.payments_info_machine'].search(
							[('description_machine_payment','=','ANTICIPO')])
						if mp:
							code_payment = mp.id_machine_payment
						else:
							code_payment = "16" #para evitar fallos
					else:
						print("no tiene medio asociado y no es anticipo poner por defecto")
						mp = invoice.env['bin_maquina_fiscal_medios_pago.payments_info_machine'].search(
							[('description_machine_payment','=','DEFAULT')])
						if mp:
							code_payment = mp.id_machine_payment
						else:
							code_payment = "16"#para evitar fallos
				
				code = code_payment
				payment["code"] = str(code.zfill(2))
				payments.append(payment)
				#print("es a credito no hay pagos asociados")"""

		else:
			print("es a credito no hay pagos asociados")
			mp = invoice.env['bin_maquina_fiscal_medios_pago.payments_info_machine'].search(
				[('description_machine_payment', '=', 'CREDITO')])
			if mp:
				code_payment = mp.id_machine_payment
			else:
				code_payment = "16"#para evitar fallos
			amount  = str(format(invoice.foreign_currency_id.round(invoice.foreign_amount_total), '.2f')).replace('.', '').zfill(12)
			payment = {"code": code_payment,"amount":amount}
			payments.append(payment)
		
		invoice_data["payments"] = payments

		itemlist = []
		for line in invoice.invoice_line_ids:
			item = {}
			item["price"] = str(format(
				invoice.foreign_currency_id.round(line.foreign_price_unit), '.2f')).replace('.', ',').zfill(11)
			item["qty"] = str(format(line.quantity,'.3f').replace('.', ',').zfill(11))
			item["code"] = "|"+line.name+"|" if line.name else ""
			item["name"] = line.product_id.name
			
			ct = '0'
			if len(line.tax_ids) > 0:
				if line.tax_ids[0].caracter_tax_machine == '!':
					ct = '1'
				elif line.tax_ids[0].caracter_tax_machine == '"':
					ct = '2'
				elif line.tax_ids[0].caracter_tax_machine == '#':
					ct = '3'
				else:
					ct = '0'
				
			item["tax"] = ct 
			itemlist.append(item)
		
		invoice_data["items"] = itemlist

		return True,invoice_data
		
	def programacion(self):
		self.printer.SendCmd("D")
		return True, "Programación impresa"

	def _is_advance_payment(self, i, invoice):
		moveobj = invoice.env['account.move'].browse(i.get("move_id"))
		for ml in moveobj.line_ids:
			if ml.payment_id_advance:
				return True
		return False

	#recibe el tipo de documento del cual devolvera el ultimo numero en maquina
	def get_last_invoice_number(self,type_doc):
		try:
			self.cerrar_puerto()
			time.sleep(2)
			success_port, msg = self.abrir_puerto()
			print("abrir puerto", msg)
			time.sleep(1)
			if success_port:
				state, error = self.estado_error()
				print("Estado", state)
				print("error", error)
				if state in ["4", "5"] and error in ["0","1"]:  # 5 en medio de op fiscal, error 1 fin en entrega de papel
					estado_s1 = self.printer.GetS1PrinterData()
					time.sleep(2)
					self.cerrar_puerto()
					if type_doc == "NC":
						number = estado_s1._lastNCNumber
					if type_doc == "FAC":
						number = estado_s1._lastInvoiceNumber
					print("este es el numero de ultima factura", number)
					return True, str(number)
				else:
					return False, "El estado de la maquina no es valido"
			else:
				print("puerto no conectado o no existe factura")
				return False, msg
		except Exception as e:
			print("exepcion", str(e))
			return False, str(e)
	#CREDITNOTE
	def print_customer_credit_note(self, invoice,machine):

		#OJOOOOOOOOOOO refund_invoice_id en teoria es la factura de origen si esta en False buscar el numero y fecha directamente
		#si es false es que fue hecha sin origen en el sistema
		try:
			if not invoice:
				return False, "Nota es obligatoria"

			self.cerrar_puerto()
			time.sleep(2)
			success_port, msg = self.abrir_puerto()
			print("abrir puerto", msg)
			time.sleep(1)
			if success_port:
				state, error = self.estado_error()
				print("Estado", state)
				print("error", error)
				if state in ["4", "5"] and error in ["0", "1"]:  # temporal
					printed, invoice_msg = self.print_credit_note_bin(invoice, machine)
					time.sleep(2)
					self.cerrar_puerto()
					return printed, invoice_msg
				else:
					return False, "El estado de la maquina no es valido"
			else:
				print("puerto no conectado o no existe factura")
				return False, msg
		except Exception as e:
			print("exepcion", str(e))
			return False, str(e)

	def print_credit_note_bin(self, invoice, machine):
		#Nota de Credito
		valid, invoice_data = self.validate_credit_note_parameter(invoice, machine)
		if valid and invoice_data:
			try:
				self.printer.SendCmd(str("iR*"+invoice_data.get("vat")))
				self.printer.SendCmd(str("iS*"+invoice_data.get("name")))
				#Factura afectada
				self.printer.SendCmd(str("iF*"+invoice_data.get("origin")))
				self.printer.SendCmd(str("iD*"+invoice_data.get("origin_date")))
				self.printer.SendCmd(str("iI*"+invoice_data.get("serial_machine")))
				
				self.printer.SendCmd(str("i00ACCION: "+invoice_data.get("action_number", "")))
				self.printer.SendCmd(str("i00TELEFONO: "+invoice_data.get("phone")))
				self.printer.SendCmd(str("i01"+invoice_data.get("company_name", "")))


				for item in invoice_data.get("items", []):
					time.sleep(1)
					self.printer.SendCmd(str("GC+"+item.get("tax")+item.get("price")+"||"+item.get("qty")+"||"+item.get("name")+item.get("code")))

				self.printer.SendCmd(str("3"))  # sub total en factura
				#poner todas como parcial
				#for payment in invoice_data.get("payments", []):
				#	cmd_success = self.printer.SendCmd(
				#		"2"+str(payment.get("code")+payment.get("amount")))
				#	print("cmd_success", cmd_success)
				#	if not cmd_success:
				#		return False, "Error enviando comando a la maquina"
				#time.sleep(1)
				#amount_due = self.get_amount_to_pay()
				#time.sleep(1)
				#print("amount due")
				#print(amount_due)
				#if amount_due > 0:
				#	self.printer.SendCmd(str("101"))
				self.printer.SendCmd(str("101"))
				print("termino de imprimir")
				return True, "Factura impresa correctamente"
			except Exception as e:
				return False, str(e)
		else:
			return False, "Algo salio mal con los parametros de la factura, verifique la informacion"
	
	def validate_credit_note_parameter(self, invoice, machine):

		invoice_data = {}
		
		if not invoice or not machine:
			return False, invoice_data

		if not invoice.partner_id.vat:
			return False, invoice_data
		else:
			invoice_data["vat"] = invoice.vat

		if not invoice.partner_id.name:
			return False, invoice_data
		else:
			invoice_data["name"] = invoice.partner_id.name
		#solo country
		if not invoice.action_number:
			#return False, invoice_data
			invoice_data["action_number"] = ""
		else:
			invoice_data["action_number"] = invoice.action_number

		if not invoice.partner_id.phone:
			return False, invoice_data
		else:
			invoice_data["phone"] = invoice.partner_id.phone

		if not invoice.company_id:
			return False, invoice_data
		else:
			invoice_data["company_name"] = invoice.company_id.name

		if invoice.reversed_entry_id:
			#es una nota con factura asociada
			if invoice.reversed_entry_id.invoice_date:
				try:
					#tomar de aqui o del numero de origen?
					if not invoice.reversed_entry_id:
						return False, {}
					#ori = invoice.origin.split("/")
					#if len(ori) >= 2:
					#invoice_number = ori[2]
					invoice_data["origin"] = str(invoice.reversed_entry_id.machine_invoice_number.zfill(11))
					date_format = invoice.reversed_entry_id.invoice_date.strftime("%d-%m-%Y")
					invoice_data["origin_date"] = date_format
					if invoice.reversed_entry_id.serial_machine:
						invoice_data["serial_machine"] = invoice.reversed_entry_id.serial_machine
				except Exception as e:
					print(str(e))
					return False, {}
			else:
				print("refund invoice do not have date")
				return False, {}
		else:
			#es una nota sin factura asociada
			#esto es una implementacion
			try:
				if not invoice.origin_country:
					return False, {}
				#origin debe tener solo el numero
				invoice_data["origin"] = str(invoice.origin_country.zfill(11))
				if not invoice.origin_date:
					return False, {}
				date_format = invoice.origin_date.strftime("%d-%m-%Y")
				invoice_data["origin_date"] = date_format
				if machine.machine_serial:
					invoice_data["serial_machine"] = machine.machine_serial
				else:
					return False, {}
			except Exception as e:
				print(str(e))
				return False, {}

		
		#recorrer todos los pagos asociados y verificar los diarios (son los medios de pago en la maquina) o anticipo y credito buscar
		#falta aclarar duda de cual pago tomar, el ejemplo tiene efectivo
		payments = []
		if not invoice.is_credit:
			for pv in invoice._get_reconciled_info_JSON_values():
				payment = {}
				amount = pv.get("amount") * invoice.foreign_currency_rate
				payment["amount"] = str(format(
					invoice.foreign_currency_id.round(amount), '.2f')).replace('.', '').zfill(12)
				journal_obj = invoice.env['account.journal'].search(
					[('name', '=', pv.get("journal_name"))])

				if journal_obj.id_machine_payment:
					code_payment = journal_obj.id_machine_payment
				else:
					print("buscar el medio de pago llamado NOTA DE CREDITO, igual verificar que es aqui")
					mp = invoice.env['bin_maquina_fiscal_medios_pago.payments_info_machine'].search([('description_machine_payment', '=', 'NOTA DE CREDITO')])
					if mp:
						code_payment = mp.id_machine_payment
					else:
						mp2 = invoice.env['bin_maquina_fiscal_medios_pago.payments_info_machine'].search([('description_machine_payment', '=', 'DEFAULT')])
						if mp2:
							code_payment = mp2.id_machine_payment
						else:
							code_payment = "16"  # para evitar fallos

				code = code_payment
				payment["code"] = str(code.zfill(2))
				print("payment",payment)
				payments.append(payment)
		else:
			print("es a credito no hay pagos asociados, nota de credito no deberia pasar")
			mp = invoice.env['bin_maquina_fiscal_medios_pago.payments_info_machine'].search(
				[('description_machine_payment', '=', 'CREDITO')])
			if mp:
				code_payment = mp.id_machine_payment
			else:
				code_payment = "16"  # para evitar fallos
			amount = str(format(invoice.foreign_currency_id.round(
				invoice.foreign_amount_total), '.2f')).replace('.', '').zfill(12)
			payment = {"code": code_payment, "amount": amount}
			payments.append(payment)

		invoice_data["payments"] = payments

		itemlist = []
		for line in invoice.invoice_line_ids:
			print("+++++++++++++++++++++++++++++++++++++++++++")
			item = {}
			
			item["price"] = str(format(
				invoice.foreign_currency_id.round(line.foreign_price_unit), '.2f')).replace('.', ',').zfill(11)
			item["qty"] = str(format(line.quantity, '.3f').replace('.', ',').zfill(11))
			item["code"] = "|"+line.name+"|" if line.name else ""
			item["name"] = line.product_id.name
			#tax = "d0"
			#if len(line.invoice_line_tax_ids) > 0:
			#	if line.invoice_line_tax_ids[0].caracter_tax_machine == "!":
			#		tax = "d1"
			#	if line.invoice_line_tax_ids[0].caracter_tax_machine == '"':
			#		tax = "d2"
			#	if line.invoice_line_tax_ids[0].caracter_tax_machine == '#':
			#		tax = "d3"
			#	if not line.invoice_line_tax_ids[0].caracter_tax_machine:
			#		tax = "d0"
			
			tax = "0"
			if len(line.tax_ids) > 0:
				if line.tax_ids[0].caracter_tax_machine == "!":
					tax = "1"
				if line.tax_ids[0].caracter_tax_machine == '"':
					tax = "2"
				if line.tax_ids[0].caracter_tax_machine == '#':
					tax = "3"
				if not line.tax_ids[0].caracter_tax_machine:
					tax = "0"	

			item["tax"] = tax
			itemlist.append(item)
		invoice_data["items"] = itemlist
		print("invoice_Data",invoice_data)
		return True, invoice_data


	def get_amount_to_pay(self):
		try:
			#self.cerrar_puerto()
			#time.sleep(2)
			#success_port, msg = self.abrir_puerto()
			#print("abrir puerto", msg)
			#time.sleep(1)
			#if success_port:
			#	state, error = self.estado_error()
			#	print("Estado", state)
			#	print("error", error)
			#	if state in ["4", "5"] and error == "0":  # temporal el 5
			estado_s2 = self.printer.GetS2PrinterData()
			time.sleep(1)
			if estado_s2:
				return estado_s2._amountPayable
			else:
				return 0
			#self.cerrar_puerto()
		except Exception as e:
			print("exepcion", str(e))
			return 0
