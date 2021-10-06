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


class utils_tax():

	def __init__(self, tipo_conexion=True, host='', port=''):
		self.printer = Tfhka(tipo_conexion, host, port)  # Tfhka.Tfhka()

	def print_taxes_info(self):
		try:
			self.cerrar_puerto()
			time.sleep(2)
			success_port, msg = self.abrir_puerto()
			time.sleep(1)
			if success_port:
				success_info, msg_tax_info = self.obtener_tax_info()
				self.estado_error()#informativo luego quitar
				time.sleep(2)
				self.cerrar_puerto()
				return success_info, msg_tax_info
			else:
				return False,msg
		except Exception as e:
			print("exepcion", str(e))
			return False,str(e)

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

	def estado_error(self):
		self.estado = self.printer.ReadFpStatus()
		try:
			return self.estado[0], self.estado[5]
		except Exception as e:
			print(e)
			return False, False

	def obtener_tax_info(self):
		try:
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
		except Exception as e:
			print("excepcion consultando tax info",str(e))
			return False,"Error consultando"

	def update_taxes_machine(self, taxes):
		try:
			if not taxes:
				return False, "Impuesto es obligatorio"

			self.cerrar_puerto()
			time.sleep(2)
			success_port, msg = self.abrir_puerto()
			time.sleep(1)
			if success_port:
				state, error = self.estado_error()
				if state == "4" and error == "0":
					success_z = self.imprimir_ReporteZ()
					time.sleep(3)
					if success_z:
						self.printer.SendCmd(str("PT"+str(taxes)))
						self.printer.SendCmd(str("Pt"))
						time.sleep(2)
						self.cerrar_puerto()
						print("ya actualizo tasas")
						return True, "Tasas actualizadas"
					else:
						time.sleep(2)
						self.cerrar_puerto()
						return False,msg_z
					
				else:
					return False, error
			else:
				print("puerto no conectado")
				return False, msg
		except Exception as e:
			print("exepcion", str(e))
			return False, str(e)

	def obtener_reporteZ(self):
		try:
			reporte = self.printer.GetZReport()
			salida = "Numero Ultimo Reporte Z: " + str(reporte._numberOfLastZReport)
			salida += "\nFecha Ultimo Reporte Z: " + str(reporte._zReportDate)
			salida += "\nHora Ultimo Reporte Z: " + str(reporte._zReportTime)
			salida += "\nNumero Ultima Factura: " + str(reporte._numberOfLastInvoice)
			salida += "\nFecha Ultima Factura: " + str(reporte._lastInvoiceDate)
			salida += "\nHora Ultima Factura: " + str(reporte._lastInvoiceTime)
			salida += "\nNumero Ultima Nota de Debito: " + \
				str(reporte._numberOfLastDebitNote)
			salida += "\nNumero Ultima Nota de Credito: " + \
				str(reporte._numberOfLastCreditNote)
			salida += "\nNumero Ultimo Doc No Fiscal: " + \
				str(reporte._numberOfLastNonFiscal)
			salida += "\nVentas Exento: " + str(reporte._freeSalesTax)
			salida += "\nBase Imponible Ventas IVA G: " + str(reporte._generalRate1Sale)
			salida += "\nImpuesto IVA G: " + str(reporte._generalRate1Tax)
			salida += "\nBase Imponible Ventas IVA R: " + str(reporte._reducedRate2Sale)
			salida += "\nImpuesto IVA R: " + str(reporte._reducedRate2Tax)
			salida += "\nBase Imponible Ventas IVA A: " + \
				str(reporte._additionalRate3Sal)
			salida += "\nImpuesto IVA A: " + str(reporte._additionalRate3Tax)
			salida += "\nNota de Debito Exento: " + str(reporte._freeTaxDebit)
			salida += "\nBI IVA G en Nota de Debito: " + str(reporte._generalRateDebit)
			salida += "\nImpuesto IVA G en Nota de Debito: " + \
				str(reporte._generalRateTaxDebit)
			salida += "\nBI IVA R en Nota de Debito: " + str(reporte._reducedRateDebit)
			salida += "\nImpuesto IVA R en Nota de Debito: " + \
				str(reporte._reducedRateTaxDebit)
			salida += "\nBI IVA A en Nota de Debito: " + \
				str(reporte._additionalRateDebit)
			salida += "\nImpuesto IVA A en Nota de Debito: " + \
				str(reporte._additionalRateTaxDebit)
			salida += "\nNota de Credito Exento: " + str(reporte._freeTaxDevolution)
			salida += "\nBI IVA G en Nota de Credito: " + \
				str(reporte._generalRateDevolution)
			salida += "\nImpuesto IVA G en Nota de Credito: " + \
				str(reporte._generalRateTaxDevolution)
			salida += "\nBI IVA R en Nota de Credito: " + \
				str(reporte._reducedRateDevolution)
			salida += "\nImpuesto IVA R en Nota de Credito: " + \
				str(reporte._reducedRateTaxDevolution)
			salida += "\nBI IVA A en Nota de Credito: " + \
				str(reporte._additionalRateDevolution)
			salida += "\nImpuesto IVA A en Nota de Credito: " + \
				str(reporte._additionalRateTaxDevolution)
			return True, salida
		except Exception as e:
			print(str(e))
			return False,"Error obteniendo reporte z"

	def imprimir_ReporteZ(self):
		self.printer.PrintZReport()
		return True
