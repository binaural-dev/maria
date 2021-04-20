# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartnerBinauralContactos(models.Model):
    _inherit = 'res.partner'
    
    def _get_configurate_supplier_islr_retention(self):
        param = self.env['ir.config_parameter']
        account_id = int(param.sudo().get_param('account_retention_islr'))
        if account_id:
            return account_id

    def _get_configurate_supplier_iva_retention(self):
        param = self.env['ir.config_parameter']
        account_id = int(param.sudo().get_param('account_retention_iva'))
        if account_id:
            return account_id

    withholding_type = fields.Many2one('type.withholding', 'Porcentaje de retención',
                                       domain="[('state','=',True)]", track_visibility='onchange')
    iva_retention = fields.Many2one('account.account', 'Cuenta de Retención de IVA para cliente', track_visibility="onchange")
    islr_retention = fields.Many2one('account.account', 'Cuenta de Retención de ISLR para cliente', track_visibility="onchange")
    taxpayer = fields.Selection([('formal', 'Formal'), ('special', 'Especial'), ('ordinary', 'Ordinario')],
                                string='Tipo de contribuyente', default='ordinary')
    type_person_ids = fields.Many2one('type.person', 'Tipo de Persona', track_visibility="onchange")

    supplier_iva_retention = fields.Many2one('account.account', 'Cuenta de Retención de IVA  para proveedor',
                                             track_visibility="onchange",
                                             default=_get_configurate_supplier_iva_retention, readonly=1)
    supplier_islr_retention = fields.Many2one('account.account', 'Cuenta de Retención de ISLR para proveedor',
                                              track_visibility="onchange",
                                              default=_get_configurate_supplier_islr_retention, readonly=1)
    exempt_islr = fields.Boolean(default=True, string='Exento ISLR', help='Indica si es exento de retencion de ISLR')
    exempt_iva = fields.Boolean(default=True, string='Exento IVA', help='Indica si es exento de retencion de IVA')
    business_name = fields.Char(string='Razón Social')

    prefix_vat = fields.Selection([
        ('v', 'V'),
        ('e', 'E'),
        ('j', 'J'),
        ('g', 'G'),
        ('c', 'C'),
    ], 'Prefijo Rif', required=True, default='v')
