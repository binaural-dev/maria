# -*- coding: utf-8 -*-

from odoo import models, api, exceptions, fields
from . import validations


class Professions(models.Model):
    _name = 'country.professions'
    _description = 'Profesiones'
    _rec_name = 'name'

    _sql_constraints = [
	    ('name_uniq', 'unique(name)', 'El nombre de la profesión ya se encuentra registrado!'),
    ]
    name = fields.Char(string='Nombre')
    active = fields.Boolean(string='Activo',default=True)

    @api.onchange('name')
    def upper_name(self):
        return validations.case_upper(self.name, "name")