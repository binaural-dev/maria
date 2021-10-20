# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class account_payment_inh_expense(models.Model):
	_inherit = 'account.payment'

	is_expense = fields.Boolean(default=False, string="Es Gasto", help="Este pago es un gasto")