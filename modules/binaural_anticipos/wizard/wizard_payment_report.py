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

_logger = logging.getLogger(__name__)


class WizardStatusBatch(models.TransientModel):
	_name = "wizard.payment.report.all"

	payment_type = fields.Selection([('outbound', 'Enviado'), ('inbound', 'Recibido')], string='Tipo de pago', required=True)

	journal_id = fields.Many2one('account.journal', string='Diario', required=True, domain=[('type', 'in', ('bank', 'cash'))])

	start_date = fields.Date(string='Fecha inicio', default=fields.Date.context_today, required=True)
	end_date = fields.Date(string='Fecha fin', default=fields.Date.context_today, required=True)

	def generate_report_payment(self):

		print("generar reporte")
		if not self.payment_type:
			raise UserError("Tipo de pago es obligatorio")
		if not self.journal_id:
			raise UserError("Diario contable es obligatorio")
		if not self.start_date:
			UserError("Fecha de inicio es obligatorio")
		if not self.end_date:
			UserError("Fecha fin es obligatorio")
		data = {'form':{'payment_type': self.payment_type, 'journal_id': self.journal_id.id,'start_date': self.start_date, 'end_date':self.end_date}}
		return self.env.ref('binaural_anticipos.action_report_all_payments').report_action(self, data=data)


