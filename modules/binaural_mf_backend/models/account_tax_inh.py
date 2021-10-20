# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, pycompat, date_utils
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import re
import uuid
import json
from odoo.addons.binaural_mf_backend.models.utils_tax import *


class AccountTaxMaquinaFiscal(models.Model):
    _inherit = 'account.tax'

    caracter_tax_machine = fields.Char(
        string="Identificador en máquina", size=1)
    tax_position = fields.Integer(string="Posición en máquina")

    def enable_machine(self):
        machine_info = self.env['bin_maquina_fiscal.machine_info'].search(
            [('active', '=', True)], limit=1)
        if machine_info:
            utils_tax2 = utils_tax(
                machine_info.local, machine_info.host, machine_info.port)
            if utils_tax2:
                return utils_tax2
            else:
                raise UserError("Error iniciando SDK")
        else:
            raise UserError("No hay maquinas fiscales configuradas")

    def update_taxes_in_machine(self,vals):
        taxes = ""
        utils_tax = self.enable_machine()
        machine_taxes = self.search(
            [('caracter_tax_machine', '!=', '')], order='tax_position asc')
        for mt in machine_taxes:
            price_include = vals.get("price_include", "1") if self.id == mt.id and vals.get("price_include", "None") != "None" else mt.price_include
            if price_include:
                include = "2" #price include
            else:
                include = "1"#not include

            amount = vals.get(
                "amount", 0) if self.id == mt.id and vals.get(
                "amount", 0) > 0 else mt.amount
            taxes += include + \
                str(format(amount, '.2f').replace('.', '').zfill(4))
        print("taxes construido",taxes)
        #success, msg = utils_tax.update_taxes_machine(taxes)
        #print("msg retornado de update taxes",msg)
        success = False #no permitir guardar
        return success

    def get_tax_info(self):
        utils_tax = self.enable_machine()
        success, msg = utils_tax.print_taxes_info()
        if success:
            raise UserError(msg)
        else:
            raise UserError(msg)

    #@api.multi
    def write(self, vals):
        success_machine_update = False
        if vals.get("amount",0) > 0 or vals.get("price_include","None") != "None" and self.caracter_tax_machine:
            #success_machine_update = self.update_taxes_in_machine(vals)
            #success_machine_update = False
            #por ahora en true, para que no intente actualizar al instalar ya que se registran los de data.xml y ejecuta el cambio
            success_machine_update = True
        else:
            success_machine_update = True
        if not success_machine_update:
            raise UserError("No se pudo actualizar la tasa en la máquina")
        return super(AccountTaxMaquinaFiscal, self).write(vals)
