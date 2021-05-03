# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrderBinauralCompras(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.onchange('filter_partner')
    def get_domain_partner(self):
        for record in self:
            record.partner_id = False
            if record.filter_partner == 'customer':
                return {'domain': {
                    'partner_id': [('customer_rank', '>=', 1)],
                }}
            elif record.filter_partner == 'supplier':
                return {'domain': {
                    'partner_id': [('supplier_rank', '>=', 1)],
                }}
            elif record.filter_partner == 'contact':
                return {'domain': {
                    'partner_id': [('supplier_rank', '=', 0), ('customer_rank', '=', 0)],
                }}
            else:
                return []

    phone = fields.Char(string='Teléfono', related='partner_id.phone')
    vat = fields.Char(string='RIF', compute='_get_vat')
    address = fields.Char(string='Dirección', related='partner_id.street')
    business_name = fields.Char(string='Razón Social', related='partner_id.business_name')
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, states=READONLY_STATES,\
                                 change_default=True, tracking=True,\
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    filter_partner = fields.Selection([('customer', 'Clientes'), ('supplier', 'Proveedores'), ('contact', 'Contactos')],
                                      string='Filtro de Contacto', default='supplier')

    @api.depends('partner_id')
    def _get_vat(self):
        for p in self:
            if p.partner_id.prefix_vat and p.partner_id.vat:
                vat = str(p.partner_id.prefix_vat) + str(p.partner_id.vat)
            else:
                vat = str(p.partner_id.vat)
            p.vat = vat