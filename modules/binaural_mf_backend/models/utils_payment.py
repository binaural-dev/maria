from odoo.addons.binaural_mf_backend.sdk_tfhka.Tfhka import Tfhka
from datetime import (timedelta, datetime as pyDateTime,
					  date as pyDate, time as pyTime)

import sys

import serial
import os
import time
from datetime import (timedelta, datetime as pyDateTime,
					  date as pyDate, time as pyTime)

import sys


class utils_payment():

	def __init__(self, tipo_conexion=True, host='', port=''):
		self.printer = Tfhka(tipo_conexion, host, port)  # Tfhka.Tfhka()

	def print_programed(self):
		try:
			self.cerrar_puerto()
			time.sleep(2)
			success_port, msg = self.abrir_puerto()
			time.sleep(1)
			if success_port:
				state, error = self.estado_error()
				if state == "4" and error == "0":
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
	def obtener_estado_maquina(self, estado):
		try:
			if not estado:
				return False, "Estado es obligatorio"

			self.cerrar_puerto()
			time.sleep(2)
			success_port, msg = self.abrir_puerto()
			time.sleep(1)
			if success_port:
				state, error = self.estado_error()
				if state == "4" and error == "0":
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

	def abrir_puerto(self):
		try:
			resp = self.printer.OpenFpctrl()
			if resp:
				return True, "Impresora Conectada Correctamente en: "
			else:
				return False, "Impresora no Conectada o Error Accediendo al Puerto"
		except serial.SerialException:
			return False, "Impresora no Conectada o Error Accediendo al Puerto"

	def cerrar_puerto(self):
		resp = self.printer.CloseFpctrl()
		if not resp:
			return True, "Impresora Desconectada"
		else:
			return False, "Error"

	def obtener_estado(self, estado):
		if estado == "S1":
			try:
				estado_s1 = self.printer.GetS1PrinterData()
				print(str(estado_s1._lastInvoiceNumber))
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
				salida += "\nNumero Ultima Nota de Credito: " + \
					str(estado_s1._lastNCNumber)
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
				salida += "\nCantidad de Reportes Z: " + \
					str(estado_s1._dailyClosureCounter)
				salida += "\nNumero de RIF: " + str(estado_s1._rif)
				salida += "\nNumero de Registro: " + \
					str(estado_s1._registeredMachineNumber)
				salida += "\nHora de la Impresora: " + str(estado_s1._currentPrinterTime)
				salida += "\nFecha de la Impresora: " + str(estado_s1._currentPrinterDate)
				return True, salida
				#self.txt_informacion.setText(salida)
			except Exception as e:
				return False, e

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
			return True, salida
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
			return self.estado[0], self.estado[5]
		except Exception as e:
			print(e)
			return False, False


	def programacion(self):
		self.printer.SendCmd("D")
		return True, "Programación impresa"

	def set_to_machine_payment(self, payment):
		try:
			self.cerrar_puerto()
			time.sleep(2)
			success_port, msg = self.abrir_puerto()
			time.sleep(1)
			if success_port:
				state, error = self.estado_error()
				if state == "4" and error == "0":
					printed, invoice_msg = self.set_to_machine(payment)
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
	
	def set_to_machine(self,payment):
		print("enviar a maquina",payment)
		if not payment:
			return False, "Medio de pago es obligatorio"
		if not payment.id_machine_payment:
			return False, "El identificador en maquina es obligatorio"
		if not payment.description_machine_payment:
			return False, "Nombre de medio de pago es obligatorio"
		payment_str = str(payment.id_machine_payment) + \
                    str(payment.description_machine_payment)
		
		s = self.printer.SendCmd("PE"+str(payment_str))

		if s:
			return True, "Pago enviado a maquina"
		else:
			return False, "Comando retorno False"

