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


class WizardEstablishExtension(models.TransientModel):
	_name = "wizard.establish.extension"

	reason = fields.Text(string='Motivo')

	new_end_date = fields.Date(string='Nueva fecha final')

	partner_to_establish = fields.Many2one('res.partner', string='Socio a establecer prorroga')

	def establish_extension(self):
		if not self.reason:
			raise UserError("Motivo es obligatorio")
		if not self.new_end_date:
			raise UserError("Nueva fecha final es obligatoria")
		if self.new_end_date <= fields.Date.today():
			raise UserError("La fecha final de suspensión debe ser mayor a la fecha actual")
		if not self.partner_to_establish:
			raise UserError("Socio a establecer prorroga es obligatorio")
		
		self.partner_to_establish.write({'end_date_partner':self.new_end_date})
		self.partner_to_establish.message_post(
				subject=_("Establecer prorroga:(%s)") % self.partner_to_establish.name,
				body=_("Prorroga establecida para %s, nueva fecha de fin del socio: %s, por el usuario %s, por el motivo: %s") % (
					self.partner_to_establish.name,
					self.new_end_date.strftime("%d/%m/%y"),
					self.env.user.name,
					self.reason,
				)
			)
		for ch in self.partner_to_establish.child_ids:
			ch.write({'end_date_partner':self.new_end_date})
