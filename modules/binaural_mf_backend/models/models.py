# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.binaural_mf_backend.models.utils_print import *
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

class bin_config_machine(models.Model):
    _name = 'bin_maquina_fiscal.machine_info'
    _rec_name = 'machine_serial'

    machine_serial = fields.Char(string='Serial de la máquina',required=True)
    machine_brand = fields.Char(string='Marca')
    machine_model = fields.Char(string='Modelo')
    machine_route = fields.Char(string='Descripcion de la ruta')
    host = fields.Char(string='Host')
    port = fields.Char(string='Puerto')
    active = fields.Boolean(string='Activo',default=True)
    local = fields.Boolean(string="Impresora conectada local")

    def get_data_programed(self):
        machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
            [('active', '=', True)], limit=1)
        if machine_info:
            utils_print2 = utils_print(
                machine_info.local, machine_info.host, machine_info.port)
            success, msg = utils_print2.print_programed()
            if success:
                print("Programación impresa")
            else:
                raise UserError(msg)
        else:
            raise UserError("No hay máquina fiscal configurada")

    def get_status(self):
        machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
            [('active', '=', True)], limit=1)
        if machine_info:
            utils_print2 = utils_print(
                machine_info.local, machine_info.host, machine_info.port)
            success, msg = utils_print2.obtener_estado_maquina("S1")
            if success:
                raise UserError(msg)
            else:
                raise UserError(msg)
        else:
            raise UserError("No hay máquina fiscal configurada")

    @api.onchange('local')
    def _onchange_local(self):
        for i in self:
            if i.local:
                array_field = ['host','port']
                return self.clear_field(array_field)


    def clear_field(self,field):
        result = {
            'value': {
            }
        }
        for field in field:
            result['value'][field] = False
        return result




