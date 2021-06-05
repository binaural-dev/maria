from odoo import api, fields, models, _, exceptions
from datetime import datetime

from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import math
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from collections import defaultdict
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import ast
import json
import re
import warnings

import logging
_logger = logging.getLogger(__name__)


class AccountRetentionBinauralLineFacturacion(models.Model):
    _name = 'account.retention.line'
    _rec_name = 'name'

    @api.depends('invoice_id')
    def _retention_rate(self):
        for record in self:
            if record.invoice_id.move_type in ['in_invoice', 'in_refund', 'in_debit']:
                record.retention_rate = record.invoice_id.partner_id.withholding_type.value

    @api.onchange('retention_amount')
    def _onchange_retention_amount(self):
        for record in self:
            if record.retention_amount > record.iva_amount:
                return {
                    'warning': {
                        'title': 'El monto retenido excedende',
                        'message': 'El monto a retener no debe superar al IVA de la factura, por favor verificar'
                    },
                    'value': {
                        'retention_amount': 0
                    },
                
                }
            if record.retention_amount > record.invoice_id.amount_residual:
                return {
                    'warning': {
                        'title': 'El monto retenido excedende',
                        'message': 'El monto a retener no debe superar el monto adeudado de la factura, por favor verificar'
                    },
                    'value': {
                        'retention_amount': 0
                    },
        
                }

    name = fields.Char('Descripción', size=64, select=True)
    currency_id = fields.Many2one(related="retention_id.company_currency_id")
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id.id)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency",
                                          readonly=True)
    retention_id = fields.Many2one('account.retention', 'Comprobante', ondelete='cascade', select=True,
                                   help="Comprobante")
    invoice_id = fields.Many2one('account.move', 'Factura', required=True, readonly=True, ondelete='cascade',
                                 select=True, help="Factura a retener")
    invoice_type = fields.Selection(selection=[
        ('out_invoice', 'Factura de Cliente'),
        ('out_refund', 'Nota de Crédito Cliente'),
        ('out_debit', 'Nota de Débito de Cliente'),
        ('in_invoice', 'Factura de Proveedor'),
        ('in_refund', 'Nota de Crédito de Proveedor'),
        ('in_debit', 'Nota de Crédito de Proveedor'),
    ], string='Tipo de Factura',)
    reference_invoice_number = fields.Char(string="Número de factura", related="invoice_id.name", store=True)
    tax_line = fields.Float(string='Alicuota')
    amount_tax_ret = fields.Float(string='Impuesto retenido',
                                  help="Total impuesto retenido de la factura")
    base_ret = fields.Float(string='Base imponible',
                            help="Base retenida de la factura")
    imp_ret = fields.Float(string='Impuesto Causado')
    retention_rate = fields.Float(compute=_retention_rate, store=True, string='Portancentaje de Retención',
                                  help="Porcentaje de Retencion ha aplicar a la factura")
    move_id = fields.Many2one('account.move', 'Movimiento Contable', help="Asiento Contable", ondelete='cascade')
    is_retention_client = fields.Boolean(string='registro de retencion de cliente', default=True)
    display_invoice_number = fields.Char(string='Display', compute='_compute_fields_combination_iva', store=True)
    
    facture_amount = fields.Float(string='Monto total del documento')
    iva_amount = fields.Float(string='Iva factura')
    retention_amount = fields.Float(string='Monto Retenido')