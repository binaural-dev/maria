# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartnerBinauralContactos(models.Model):
    _inherit = 'res.partner'
    
    def _get_configurate_supplier_retention(self):
        param = self.env['ir.config_parameter']
        islr_account_id = int(param.sudo().get_param('account_retention_islr'))
        iva_account_id = int(param.sudo().get_param('account_retention_iva'))
        if islr_account_id and iva_account_id:
            return islr_account_id, iva_account_id
        elif islr_account_id and not iva_account_id:
            return islr_account_id, False
        elif not islr_account_id and iva_account_id:
            return False, iva_account_id
        else:
            return False, False

    withholding_type = fields.Many2one('type.withholding', 'Porcentaje de retención',
                                       domain="[('state','=',True)]", track_visibility='onchange')
    iva_retention = fields.Many2one('account.account', 'Cuenta de Retención de IVA para cliente', track_visibility="onchange")
    islr_retention = fields.Many2one('account.account', 'Cuenta de Retención de ISLR para cliente', track_visibility="onchange")
    taxpayer = fields.Selection([('formal', 'Formal'), ('special', 'Especial'), ('ordinary', 'Ordinario')],
                                string='Tipo de contribuyente', default='ordinary')
    type_person_ids = fields.Many2one('type.person', 'Tipo de Persona', track_visibility="onchange")

    supplier_iva_retention = fields.Many2one('account.account', 'Cuenta de Retención de IVA  para proveedor',
                                             track_visibility="onchange",
                                             default=lambda self: self._get_configurate_supplier_retention[1], readonly=1)
    supplier_islr_retention = fields.Many2one('account.account', 'Cuenta de Retención de ISLR para proveedor',
                                              track_visibility="onchange",
                                              default=lambda self: self._get_configurate_supplier_retention[0], readonly=1)
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
