# -*- coding: utf-8 -*-

from odoo import models, api, exceptions, fields


class ActionPartner(models.Model):
    _name = 'action.partner'
    _description = 'Acciones de socios'
    _rec_name = 'number'

    _sql_constraints = [
	    ('number_uniq', 'unique(number)', 'El número de acción ya se encuentra registrado!'),
    ]

    type_action = fields.Selection([
        ('action', 'Acción'),
        ('extention', 'Extensión'),
    ], 'Tipo de Acción', default='action', required=True,track_visibility='onchange')
    number = fields.Char('Número', required=True,track_visibility='onchange')
    state = fields.Selection([
        ('active', 'Activa'),
        ('special', 'Especial'),
        ('honorary', 'Honorario'),
        ('treasury', 'Tesorería'),
    ], 'Estado', default='active', required=True,track_visibility='onchange')
    partners_previous_ids = fields.One2many('action.partner.previous', 'action_id', string='Socios Anteriores',track_visibility='onchange')


class ActionPartnerPrevious(models.Model):
    _name = 'action.partner.previous'
    _description = 'Acciones de socios anteriores'

    name = fields.Char('Nombre')
    identification = fields.Char('Cédula')
    date_start = fields.Datetime('Fecha de inicio')
    date_end = fields.Datetime('Fecha fin')
    action_id = fields.Many2one('action.partner', string='Acción')
    type_operation = fields.Selection([
        ('link', 'Vinculado'),
        ('unlink', 'Desvinculado'),
    ], string='Tipo operación')
    name_exec = fields.Char(string='Usuario')
    date_exec = fields.Date(string='Fecha operación')
