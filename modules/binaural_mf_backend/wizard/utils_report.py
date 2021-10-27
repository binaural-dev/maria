from odoo.addons.binaural_mf_backend.sdk_tfhka.Tfhka import Tfhka
from datetime import (timedelta, datetime as pyDateTime,
                      date as pyDate, time as pyTime)

import sys

import serial
import os
import time
from datetime import (timedelta, datetime as pyDateTime,
                      date as pyDate, time as pyTime)
from odoo import api, fields, SUPERUSER_ID
import sys


class utils_report():

	def __init__(self, tipo_conexion=True, host='', port=''):
		self.printer = Tfhka(tipo_conexion, host, port)  # Tfhka.Tfhka()

	def reprint_report_machine(self, data):
		print("llamar a funcion que imprime")
		if not data.number:
			return False, "Número de reporte es obligatorio"
		if len(str(data.number)) > 4 or data.number == 0:
			return False,"Número incorrecto"
		if not data.type_report:
			return False, "Tipo de reporte es obligatorio"
		
		self.cerrar_puerto()
		time.sleep(2)
		success_port, msg = self.abrir_puerto()
		time.sleep(1)
		if success_port:
			state, error = self.estado_error()
			if state == "4" and error == "0":
				time.sleep(2)
				com = str("R"+data.type_report+str(data.number).zfill(7) +
				          str(data.number).zfill(7))
				print(com)
				printed = self.printer.SendCmd(com)
				self.cerrar_puerto()
				return printed, "Reporte reimpreso"
			else:
				return False, error
		else:
			print("puerto no conectado")
			return False, msg

	def print_x_report(self):
		self.cerrar_puerto()
		time.sleep(2)
		success_port, msg = self.abrir_puerto()
		time.sleep(1)
		if success_port:
			state, error = self.estado_error()
			if state == "4" and error == "0":
				time.sleep(2)
				printed = self.printer.SendCmd("I0X")
				self.cerrar_puerto()
				return printed, "Reporte X impreso"
			else:
				return False, error
		else:
			print("puerto no conectado")
			return False, msg

	def print_z_report(self):
		self.cerrar_puerto()
		time.sleep(2)
		success_port, msg = self.abrir_puerto()
		time.sleep(1)
		if success_port:
			state, error = self.estado_error()
			if state == "4" and error == "0":
				time.sleep(2)
				printed = self.printer.SendCmd("I0Z")
				self.cerrar_puerto()
				return printed, "Reporte Z impreso"
			else:
				return False, error
		else:
			print("puerto no conectado")
			return False, msg



	def cerrar_puerto(self):
		resp = self.printer.CloseFpctrl()
		if not resp:
			return True, "Impresora Desconectada"
		else:
			return False, "Error"

	def abrir_puerto(self):
		try:
			resp = self.printer.OpenFpctrl()
			if resp:
				return True, "Impresora Conectada Correctamente en: "
			else:
				return False, "Impresora no Conectada o Error Accediendo al Puertox"
		except serial.SerialException:
			return False, "Impresora no Conectada o Error Accediendo al Puertoz"

	def estado_error(self):
		self.estado = self.printer.ReadFpStatus()
		try:
			print("ESTADO BRUTO:", str(self.estado))
			return self.estado[0], self.estado[5]
		except Exception as e:
			print(e)
			return False, False
