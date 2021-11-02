# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.addons.binaural_mf_backend.models.utils_payment import *
class bin_config_payments_machine(models.Model):
    _name = 'bin_maquina_fiscal_medios_pago.payments_info_machine'
    _rec_name = 'description_machine_payment'

    id_machine_payment = fields.Char(
        string="Identificador en máquina", size=2)
    description_machine_payment = fields.Char(string="Descripción en máquina")#este debe ser el nombre en maquina debe ser exacto porque se buscara por este nombre
    active = fields.Boolean(string='Activo', default=True)

    def action_sent_ot_machine(self):
        machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
            [('active', '=', True)], limit=1)
        if machine_info:
            utils_print2 = utils_payment(
                machine_info.local, machine_info.host, machine_info.port)
            success, msg = utils_print2.set_to_machine_payment(self)
            if success:
                print("enviado a maquina",str(msg))  # temporal
                raise UserError(msg)
            else:
                raise UserError(msg)
        else:
            raise UserError("No hay máquina fiscal configurada")

    def get_payment_info(self):
        machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
            [('active', '=', True)], limit=1)
        if machine_info:
            utils_print2 = utils_payment(
                machine_info.local, machine_info.host, machine_info.port)
            success, msg = utils_print2.print_programed()
            if success:
                print("programacion impresa")  # temporal
                raise UserError(msg)
            else:
                raise UserError(msg)
        else:
            raise UserError("No hay máquina fiscal configurada")
