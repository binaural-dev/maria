# -*- coding: utf-8 -*-

from numpy import require
from odoo import models, fields, api
from lxml import etree
import json

import logging
_logger = logging.getLogger(__name__)


class ResPartnerBinauralContactos(models.Model):
    _inherit = 'res.partner'

    @api.model
    def default_get(self, fields):
        result = super(ResPartnerBinauralContactos, self).default_get(fields)
        param = self.env['ir.config_parameter']
        islr_account_id = int(param.sudo().get_param('account_retention_islr'))
        iva_account_id = int(param.sudo().get_param('account_retention_iva'))
        result['supplier_iva_retention'] = iva_account_id
        result['supplier_islr_retention'] = islr_account_id
        return result

    withholding_type = fields.Many2one('type.withholding', 'Porcentaje de retención',
                                       domain="[('state','=',True)]", track_visibility='onchange')
    iva_retention = fields.Many2one(
        'account.account', 'Cuenta de Retención de IVA para cliente', track_visibility="onchange")
    islr_retention = fields.Many2one(
        'account.account', 'Cuenta de Retención de ISLR para cliente', track_visibility="onchange")
    taxpayer = fields.Selection([('formal', 'Formal'), ('special', 'Especial'), ('ordinary', 'Ordinario')],
                                string='Tipo de contribuyente', default='ordinary')
    type_person_ids = fields.Many2one(
        'type.person', 'Tipo de Persona', track_visibility="onchange")

    supplier_iva_retention = fields.Many2one('account.account', 'Cuenta de Retención de IVA  para proveedor',
                                             track_visibility="onchange", readonly=1)
    supplier_islr_retention = fields.Many2one('account.account', 'Cuenta de Retención de ISLR para proveedor',
                                              track_visibility="onchange", readonly=1)
    exempt_islr = fields.Boolean(
        default=True, string='Exento ISLR', help='Indica si es exento de retencion de ISLR')
    exempt_iva = fields.Boolean(
        default=True, string='Exento IVA', help='Indica si es exento de retencion de IVA')
    business_name = fields.Char(string='Razón Social')

    municipality_id = fields.Many2one(
        'res.country.municipality', string='Municipio', domain="[('state_id','=',state_id)]")

    prefix_vat = fields.Selection([
        ('V', 'V'),
        ('E', 'E'),
        ('J', 'J'),
        ('G', 'G'),
        ('C', 'C'),
        ('P', 'P'),
    ], 'Prefijo Rif', required=False, default='V')
    city_id = fields.Many2one(
        'res.country.city', 'Ciudad', track_visibility='onchange')

    economic_activity_id = fields.Many2one(
        'economic.activity', string='Actividad Económica')
    activity = fields.Text(string='Actividad Económica',
                           related="economic_activity_id.description")
    aliquot = fields.Float(
        string='Alíquota', related="economic_activity_id.aliquot")

    @api.constrains('city_id')
    def _update_city(self):
        for record in self:
            if record.city_id:
                record.city = record.city_id.name
                
    @api.onchange('state_id')
    def on_change_state(self):
        self.municipality_id = None

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id,
                                      view_type=view_type, toolbar=toolbar, submenu=submenu)
        municipality_retention = self.env["ir.config_parameter"].sudo(
        ).get_param("use_municipal_retention")
        context = dict(self._context or {})
        if municipality_retention and view_type == "form":
            doc = etree.XML(res["arch"])
            municipality_field = doc.xpath(
                "//field[@name='municipality_id']")[0]

            modifiers_field = json.loads(
                municipality_field.get("modifiers") or '{}')
            modifiers_field['required'] = True
            municipality_field.set('modifiers', json.dumps(modifiers_field))
            if not 'params' in context or not 'params' in context and not 'id' in context['params']:
                res["arch"] = etree.tostring(doc, encoding="unicode")
                return res

            record = self.env['res.partner'].browse(context['params']['id'])

            if record and record.supplier_rank > 0:
                municipality_page = doc.xpath(
                    "//notebook/page[@name='municipality_taxes']")[0]
                modifiers_page = json.loads(
                    municipality_page.get("modifiers") or '{}')
                modifiers_page['invisible'] = False
                municipality_page.set('modifiers', json.dumps(modifiers_page))

            else:
                municipality_page = doc.xpath(
                    "//notebook/page[@name='municipality_taxes']")[0]
                modifiers_page = json.loads(
                    municipality_page.get("modifiers") or '{}')
                modifiers_page['invisible'] = True
                municipality_page.set('modifiers', json.dumps(modifiers_page))

            res["arch"] = etree.tostring(doc, encoding="unicode")

        elif not municipality_retention and view_type == "form":
            doc = etree.XML(res["arch"])
            municipality_field = doc.xpath(
                "//field[@name='municipality_id']")[0]

            modifiers_field = json.loads(
                municipality_field.get("modifiers") or '{}')
            modifiers_field['required'] = False
            municipality_field.set('modifiers', json.dumps(modifiers_field))

            municipality_page = doc.xpath(
                "//notebook/page[@name='municipality_taxes']")[0]
            modifiers_page = json.loads(
                municipality_page.get("modifiers") or '{}')
            modifiers_page['invisible'] = True
            municipality_page.set('modifiers', json.dumps(modifiers_page))

            res["arch"] = etree.tostring(doc, encoding="unicode")

        return res
