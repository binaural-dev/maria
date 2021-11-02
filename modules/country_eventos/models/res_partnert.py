# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _, http


class FrecuentPartnerExtendCe(models.Model):
    _name = 'frecuent.partner'

    prefix_vat = fields.Selection([
        ('v', 'V'),
        ('e', 'E'),
        ('j', 'J'),
        ('g', 'G'),
        ('c', 'C'),
    ], 'Prefijo Rif')
    vat = fields.Char(string='RIF')
    email = fields.Char(string='Correo')
    phone = fields.Char(string='Telefono')
    name = fields.Char(string='Nombre')


class FrecuentPartnerRelation(models.Model):
    _name = 'frecuent.partner.relation'

    active = fields.Boolean('Estatus')
    frecuent_partner_id = fields.Many2one('frecuent.partner', string="Contacto Frecuente")
    partner_id = fields.Many2one('res.partner', string="Socio")


class ResPartnerExtendCe(models.Model):
    _inherit = 'res.partner'

    frecuent_contact_ids = fields.One2many('frecuent.partner.relation', 'partner_id', string="Contactos Frecuentes")
