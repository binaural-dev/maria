# -*- coding: utf-8 -*-

from odoo import models, fields, api


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
    iva_retention = fields.Many2one('account.account', 'Cuenta de Retención de IVA para cliente', track_visibility="onchange")
    islr_retention = fields.Many2one('account.account', 'Cuenta de Retención de ISLR para cliente', track_visibility="onchange")
    taxpayer = fields.Selection([('formal', 'Formal'), ('special', 'Especial'), ('ordinary', 'Ordinario')],
                                string='Tipo de contribuyente', default='ordinary')
    type_person_ids = fields.Many2one('type.person', 'Tipo de Persona', track_visibility="onchange")

    supplier_iva_retention = fields.Many2one('account.account', 'Cuenta de Retención de IVA  para proveedor',
                                             track_visibility="onchange", readonly=1)
    supplier_islr_retention = fields.Many2one('account.account', 'Cuenta de Retención de ISLR para proveedor',
                                              track_visibility="onchange", readonly=1)
    exempt_islr = fields.Boolean(default=True, string='Exento ISLR', help='Indica si es exento de retencion de ISLR')
    exempt_iva = fields.Boolean(default=True, string='Exento IVA', help='Indica si es exento de retencion de IVA')
    business_name = fields.Char(string='Razón Social')

    prefix_vat = fields.Selection([
        ('V', 'V'),
        ('E', 'E'),
        ('J', 'J'),
        ('G', 'G'),
        ('C', 'C'),
        ('P', 'P'),
    ], 'Prefijo Rif', required=False, default='V')
    city_id = fields.Many2one('res.country.city', 'Ciudad', track_visibility='onchange')

    @api.constrains('city_id')
    def _update_city(self):
        for record in self:
            if record.city_id:
                record.city = record.city_id.name
