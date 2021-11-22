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


class WizardActionBatch(models.TransientModel):
	_name = "wizard.status.action.batch"

	status = fields.Selection([
		('active', 'Activa'),
		('special', 'Especial'),
		('honorary', 'Honorario'),
		('treasury', 'Tesorería'),
	], 'Nuevo Estado', required=True)

	actions_ids = fields.Many2many('action.partner', string='Acciones',required=True)

	def change_status(self):

		if not self.status:
			raise UserError("Nuevo estado es obligatorio")
		if not self.actions_ids:
			raise UserError("Acciones obligatorias")
		for p in self.actions_ids:
			p.update({'state':self.status})

		message_id = self.env['message.wizard'].create({'message': _("Accciones actualizadas")})
		return {
			'name': _('Éxito'),
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'message.wizard',
			# pass the id
			'res_id': message_id.id,
			'target': 'new'
		}

