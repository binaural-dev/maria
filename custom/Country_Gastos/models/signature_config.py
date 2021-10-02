# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
import pytz

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError


class SignatureConfigExpenseSheet(models.Model):
    _name = "hr_expense.signature_config"
    _description = "Configuracion de firma para informe de gastos"
    _rec_name = "description"
    #email = fields.Char(string='Correo electronico')
    description = fields.Char(string='Descripcion')
    signature = fields.Binary(string='Firma')
    active = fields.Boolean(string='Activo', default=True)
