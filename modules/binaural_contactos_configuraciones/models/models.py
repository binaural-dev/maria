# -*- coding: utf-8 -*-

from odoo import models, fields, api
from . import validations


class TypeWithholdingsBinauralContactos(models.Model):
    _name = 'type.withholding'
    _description = 'Tipo de retención'
    _order = 'create_date desc'
    _sql_constraints = [('unique_name', 'UNIQUE(name)', 'No puedes agregar retenciones con el mismo nombre')]
    
    name = fields.Char(string="Nombre")
    value = fields.Float(string="Valor")
    state = fields.Boolean(default=True, string="Activo")

    @api.onchange('name')
    def upper_name(self):
        return validations.case_upper(self.name, "name")

    @api.onchange('value')
    def onchange_template_id(self):
        res = {}
        if self.value:
            res = {'warning': {
                'title': ('Advertencia'),
                'message': ('Recuerda usar coma (,) como separador de decimales')
                }
            }
    
        if res:
            return res
        
        
class TypePersonBinauralContactos(models.Model):
    _name = "type.person"
    _description = "Tipo de Persona"

    name = fields.Char(string='Descripción', required=True)
    state = fields.Boolean(default=True, string="Activo")
