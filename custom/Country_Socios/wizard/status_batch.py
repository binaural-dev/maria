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
	_name = "wizard.status.partner.batch"

	status = fields.Selection([
		('active', 'Activo'),
		('holder', 'Tenedor'),
		('deceased', 'Fallecido'),
		#('discontinued', 'Suspendido'),
		('inactive', 'Inactivo'),
	], 'Nuevo Estado', required=True)

	partners_ids = fields.Many2many('res.partner', string='Socios',required=True,domain=[('customer_rank','>',0)])

	def change_status(self):
		if not self.status:
			raise UserError("Nuevo estado es obligatorio")
		if not self.partners_ids:
			raise UserError("Socios obligatorios")
		for p in self.partners_ids:
			p.update({'state_partner':self.status})

		message_id = self.env['message.wizard'].create({'message': _("Socios actualizados")})
		return {
			'name': _('Éxito'),
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'message.wizard',
			# pass the id
			'res_id': message_id.id,
			'target': 'new'
		}
		#return True


class MessageWizard(models.TransientModel):
	_name = 'message.wizard'

	message = fields.Text('Message', required=True)

	def action_ok(self):
		""" close wizard"""
		return {'type': 'ir.actions.act_window_close'}
