# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, pycompat, date_utils
from num2words import num2words
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class InvoiceCountryFields(models.Model):
	_inherit = 'account.move'

	fee_period = fields.Date(string='Periodo de la cuota')

	pay_soon = fields.Boolean(string='Pronto Pago')

