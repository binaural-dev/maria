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
                record.invoice_type = record.invoice_id.move_type

    @api.onchange('retention_amount')
    def _onchange_retention_amount(self):
        for record in self:
            if record.retention_amount > record.iva_amount and record.retention_id.type_retention in ['iva']:
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

    @api.onchange('porcentage_retention')
    def _onchange_porcentage_retention(self):
        for record in self:
            return {
                'value': {
                    'retention_amount': record.facture_amount * (record.porcentage_retention/100)
                },
            }

    @api.depends('payment_concept_id', 'invoice_id')
    def _get_value_related(self):
        for record in self:
            if record.payment_concept_id:
                for line in record.payment_concept_id.line_payment_concept_ids:
                    if record.invoice_id.partner_id.type_person_ids.id == line.type_person_ids.id:
                        record.related_pay_from = line.pay_from
                        record.related_percentage_tax_base = line.percentage_tax_base
                        record.related_percentage_tariffs = line.tariffs_ids.percentage
                        record.related_amount_sustract_tariffs = line.tariffs_ids.amount_sustract
            if record.invoice_id:
                record.facture_total = record.invoice_id.amount_total
                record.facture_amount = record.invoice_id.amount_untaxed
                record.iva_amount = record.invoice_id.amount_tax
            if record.payment_concept_id and record.invoice_id:
                if record.facture_amount > record.related_pay_from:
                    record.retention_amount = record.facture_amount * (record.related_percentage_tax_base/100) * (record.related_percentage_tariffs/100) - record.related_amount_sustract_tariffs
                
    name = fields.Char('Descripción', size=64, select=True, required=True, default="Retención ISLR")
    currency_id = fields.Many2one(related="retention_id.company_currency_id")
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id.id)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency",
                                          readonly=True)
    retention_id = fields.Many2one('account.retention', 'Comprobante', ondelete='cascade', select=True,
                                   help="Comprobante")
    invoice_id = fields.Many2one('account.move', 'Factura', required=True, ondelete='cascade',
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
    
    facture_amount = fields.Float(string='Base Imponible')
    facture_total = fields.Float(string='Total Facturado')
    iva_amount = fields.Float(string='Iva factura')
    retention_amount = fields.Float(string='Monto Retenido')

    payment_concept_id = fields.Many2one('payment.concept', 'Concepto de pago', ondelete='cascade', select=True)
    
    #Campos para uso en ISLR
    porcentage_retention = fields.Float(string='% Retención')

    related_pay_from = fields.Float(string='Pagos desde', compute=_get_value_related, store=True)
    related_percentage_tax_base = fields.Float(string='% Base Imponible', compute=_get_value_related, store=True)
    related_percentage_tariffs = fields.Float(string='% Tarifa', compute=_get_value_related, store=True)
    related_amount_sustract_tariffs = fields.Float(string='Sustraendo', compute=_get_value_related, store=True)
