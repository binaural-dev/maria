# -*- coding: utf-8 -*-

import string
from odoo import models, fields, api
from lxml import etree
import json


class InheritedResCompany(models.Model):
    _inherit = 'res.company'

    logo_hacienda = fields.Image(string="Logo de Hacienda")
    name_hacienda = fields.Char(string="Nombre de Hacienda")
    economic_activity_number = fields.Char(
        string="Número de actividad económica")

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id,
                                      view_type=view_type, toolbar=toolbar, submenu=submenu)
        municipality_retention = self.env["ir.config_parameter"].sudo(
        ).get_param("use_municipal_retention")

        if municipality_retention and view_type == "form":
            doc = etree.XML(res["arch"])

            # invisible logo hacienda
            logo_hacienda_field = doc.xpath(
                "//field[@name='logo_hacienda']")[0]
            modifiers_logo = json.loads(
                logo_hacienda_field.get("modifiers") or '{}')
            modifiers_logo['invisible'] = False
            modifiers_logo['required'] = True
            logo_hacienda_field.set('modifiers', json.dumps(modifiers_logo))

            # invisible nombre hacienda
            name_hacienda_field = doc.xpath(
                "//field[@name='name_hacienda']")[0]
            modifiers_name_hacienda = json.loads(
                name_hacienda_field.get("modifiers") or '{}')
            modifiers_name_hacienda['invisible'] = False
            modifiers_name_hacienda['required'] = True
            name_hacienda_field.set(
                'modifiers', json.dumps(modifiers_name_hacienda))

            # invisible numero de actividad económica
            economic_activity_number_field = doc.xpath(
                "//field[@name='economic_activity_number']")[0]
            modifiers_economic_activity_number = json.loads(
                economic_activity_number_field.get("modifiers") or '{}')
            modifiers_economic_activity_number['invisible'] = False
            modifiers_economic_activity_number['required'] = True
            economic_activity_number_field.set(
                'modifiers', json.dumps(modifiers_economic_activity_number))
            
            municipality_page = doc.xpath(
                "//notebook/page[@name='datos_hacienda']")[0]
            modifiers_page = json.loads(
                municipality_page.get("modifiers") or '{}')
            modifiers_page['invisible'] = False
            municipality_page.set('modifiers', json.dumps(modifiers_page))

            res["arch"] = etree.tostring(doc, encoding="unicode")
        elif not municipality_retention and view_type == "form":
            doc = etree.XML(res["arch"])

            # invisible logo hacienda
            logo_hacienda_field = doc.xpath(
                "//field[@name='logo_hacienda']")[0]
            modifiers_logo = json.loads(
                logo_hacienda_field.get("modifiers") or '{}')
            modifiers_logo['invisible'] = True
            logo_hacienda_field.set('modifiers', json.dumps(modifiers_logo))

            # invisible nombre hacienda
            name_hacienda_field = doc.xpath(
                "//field[@name='name_hacienda']")[0]
            modifiers_name_hacienda = json.loads(
                name_hacienda_field.get("modifiers") or '{}')
            modifiers_name_hacienda['invisible'] = True
            name_hacienda_field.set(
                'modifiers', json.dumps(modifiers_name_hacienda))

            # invisible numero de actividad económica
            economic_activity_number_field = doc.xpath(
                "//field[@name='economic_activity_number']")[0]
            modifiers_economic_activity_number = json.loads(
                economic_activity_number_field.get("modifiers") or '{}')
            modifiers_economic_activity_number['invisible'] = True
            economic_activity_number_field.set(
                'modifiers', json.dumps(modifiers_economic_activity_number))
            
            municipality_page = doc.xpath(
                "//notebook/page[@name='datos_hacienda']")[0]
            modifiers_page = json.loads(
                municipality_page.get("modifiers") or '{}')
            modifiers_page['invisible'] = True
            municipality_page.set('modifiers', json.dumps(modifiers_page))
            
            res["arch"] = etree.tostring(doc, encoding="unicode")

        return res
