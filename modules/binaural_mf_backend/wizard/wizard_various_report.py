# -*- coding: utf-8 -*-

from odoo import api, fields, exceptions, http, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

from datetime import date
from dateutil.relativedelta import relativedelta
import logging
import time

from collections import OrderedDict
from odoo.addons.binaural_mf_backend.wizard.utils_report import *
_logger = logging.getLogger(__name__)


class WizardVariousReport(models.TransientModel):
	_name = "wizard.various.reports.fiscal.machine"
	"""date_start = fields.Date(
		'Fecha de Inicio', default=date.today().replace(day=1))
	date_end = fields.Date('Fecha Final',
                        default=date.today().replace(day=1) + relativedelta(months=1, days=-1))"""

	type_report = fields.Selection(
		[('X', 'Reporte X'), ('Z', 'Reporte Z')], string='Tipo de reporte', required=True)
	#Facturas/ND/NC/Reporte Z/Reporte X/Resumen Total
	#@api.one
	def print_various_report(self):
		machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
                    [('active', '=', True)], limit=1)
		if machine_info:
			utils_print2 = utils_report(
				machine_info.local, machine_info.host, machine_info.port)
			if self.type_report == "X":
				success, msg = utils_print2.print_x_report()
			elif self.type_report == "Z":
				success, msg = utils_print2.print_z_report()
			if success:
				return msg
			else:
				raise UserError(msg)
		else:
			raise UserError("No hay máquina fiscal configurada")
