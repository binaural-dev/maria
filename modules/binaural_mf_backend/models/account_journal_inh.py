# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, pycompat, date_utils
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import re
import uuid
import json
from odoo.addons.binaural_mf_backend.models.utils_payment import *


class AccountJorunalBinMachine(models.Model):
    _inherit = 'account.journal'

    id_machine_payment = fields.Char(
        string="Identificador en máquina", size=2)
    description_machine_payment = fields.Char(string="Descripción en máquina")


    def get_payment_info(self):
        machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
            [('active', '=', True)], limit=1)
        if machine_info:
            utils_print2 = utils_payment(
                machine_info.local, machine_info.host, machine_info.port)
            success, msg = utils_print2.print_programed()
            if success:
                print("programacion impresa")#temporal
                raise UserError(msg)
            else:
                raise UserError(msg)
        else:
            raise UserError("No hay máquina fiscal configurada")

    def get_payment_info_data(self):
        machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
            [('active', '=', True)], limit=1)
        if machine_info:
            utils_print2 = utils_payment(
                machine_info.local, machine_info.host, machine_info.port)
            success, msg = utils_print2.obtener_estado_maquina("S4")
            if success:
                print(msg)
                raise UserError(msg)
            else:
                raise UserError(msg)
        else:
            raise UserError("No hay máquina fiscal configurada")

