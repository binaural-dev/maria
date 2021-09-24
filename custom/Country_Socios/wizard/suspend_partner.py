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


class WizardSuspendPartner(models.TransientModel):
	_name = "wizard.suspend.partner"

	reason = fields.Text(string='Motivo')

	end_date_suspend = fields.Date(string='Fecha final de suspensión')

	partner_to_suspend = fields.Many2one('res.partner', string='Socio a suspender')

	def suspend_partner(self):
		if not self.reason:
			raise UserError("Motivo es obligatorio")
		if not self.end_date_suspend:
			raise UserError("Fecha final de suspensión es obligatoria")
		if self.end_date_suspend <= fields.Date.today():
			raise UserError("La fecha final de suspensión debe ser mayor a la fecha actual")
		if not self.partner_to_suspend:
			raise UserError("Socio a suspender es obligatorio")
		
		self.partner_to_suspend.write({'can_access_club':False,'reason':self.reason,'end_date_suspend':self.end_date_suspend,'start_date_suspend':fields.Date.today(),'user_suspend':self.env.uid,'prev_state_partner':self.partner_to_suspend.state_partner})#'state_partner':'discontinued'
		self.partner_to_suspend.message_post(
				subject=_("Socio suspendido:(%s)") % self.partner_to_suspend.name,
				body=_("Socio %s suspendido desde: %s hasta: %s, por el usuario %s, por el motivo: %s") % (
					self.partner_to_suspend.name,
					fields.Date.today().strftime("%d/%m/%y"),
					self.end_date_suspend.strftime("%d/%m/%y"),
					self.env.user.name,
					self.reason,
				)
			)
		if self.partner_to_suspend.type == 'contact' and self.partner_to_suspend.parent_id:
			self.partner_to_suspend.parent_id.message_post(
				subject=_("Carga familiar suspendido:(%s)") % self.partner_to_suspend.name,
				body=_("Carga familiar: %s suspendido desde: %s hasta: %s, por el usuario %s, por el motivo: %s") % (
					self.partner_to_suspend.name,
					fields.Date.today().strftime("%d/%m/%y"),
					self.end_date_suspend.strftime("%d/%m/%y"),
					self.env.user.name,
					self.reason,
				)
			)

class WizardRemoveSuspendPartner(models.TransientModel):
	_name = "wizard.remove.suspend.partner"

	partner_to_remove_suspend = fields.Many2one('res.partner', string='Socio a remover suspensión')

	def remove_suspend_auto(self):
		partners_to_remove = self.env['res.partner'].search([('active','=',True),('can_access_club','=',False),('end_date_suspend','=',fields.Date.today())])#,('state_partner','=','discontinued')
		for p in partners_to_remove:
			p.write({'date_remove_suspend':fields.Date.today(),'can_access_club':True,'user_remove_suspend':self.env.uid,'state_partner':p.prev_state_partner,'prev_state_partner':p.state_partner})
			if p.type == 'contact' and p.parent_id:
				p.parent_id.message_post(
					subject=_("Suspensión removida:(%s)") % p.name,
					body=_("Suspensión de la carga familiar %s removida el: %s, Automaticamente") % (
						p.name,
						fields.Date.today().strftime("%d/%m/%y"),
					)
				)
			else:			
				p.message_post(
					subject=_("Suspensión removida:(%s)") % p.name,
					body=_("Suspensión del socio %s removida el: %s, Automaticamente") % (
						p.name,
						fields.Date.today().strftime("%d/%m/%y"),
					)
				)

	def remove_suspend_partner(self):
		if not self.partner_to_remove_suspend:
			raise UserError("Socio a remover suspensión es obligatorio")
		self.partner_to_remove_suspend.write({'date_remove_suspend':fields.Date.today(),'can_access_club':True,'user_remove_suspend':self.env.uid,'state_partner':self.partner_to_remove_suspend.prev_state_partner,'prev_state_partner':self.partner_to_remove_suspend.state_partner})
		
		if self.partner_to_remove_suspend.type == 'contact' and self.partner_to_remove_suspend.parent_id:
			self.partner_to_remove_suspend.parent_id.message_post(
				subject=_("Suspensión removida:(%s)") % self.partner_to_remove_suspend.name,
				body=_("Suspensión de la carga familiar %s removida el: %s, por el usuario %s manualmente") % (
					self.partner_to_remove_suspend.name,
					fields.Date.today().strftime("%d/%m/%y"),
					self.env.user.name,
				)
			)
		else:
			self.partner_to_remove_suspend.message_post(
				subject=_("Suspensión removida:(%s)") % self.partner_to_remove_suspend.name,
				body=_("Suspensión del socio %s removida el: %s, por el usuario %s manualmente") % (
					self.partner_to_remove_suspend.name,
					fields.Date.today().strftime("%d/%m/%y"),
					self.env.user.name,
				)
			)