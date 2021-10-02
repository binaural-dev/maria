# -*- coding: utf-8 -*-

from odoo import models, api, exceptions, fields, _

from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import timedelta


class ResUsersInh(models.Model):
	_inherit = 'res.users'

	partner_id = fields.Many2one('res.partner', required=False, ondelete='restrict', auto_join=True,string='Related Partner', help='Partner-related data of the user')