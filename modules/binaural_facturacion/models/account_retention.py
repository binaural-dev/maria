from odoo import api, fields, models, _, exceptions
from datetime import datetime

from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
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


class AccountRetentionBinauralFacturacion(models.Model):
    _name = 'account.retention'
    _rec_name = 'number'

    @api.onchange('partner_id')
    def partner_id_onchange(self):
        data = []
        self.retention_line = False
        if self.type == 'out_invoice' and self.partner_id:  # Rentention of client
            if self.partner_id.taxpayer != 'ordinary':
                for facture_line_retention in self.env['account.move'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_type', 'in', ['out_invoice', 'out_debit', 'out_refund', 'out_contingence']),
                         ('state', '=', 'posted')]):
                    if not facture_line_retention.apply_retention_iva and facture_line_retention.move_type != 'out_refund' and facture_line_retention.amount_tax > 0 and facture_line_retention.payment_state in ['not_paid', 'partial']:
                        for tax in facture_line_retention.amount_by_group:
                            tax_id = self.env['account.tax'].search([('tax_group_id', '=', tax[6]), ('type_tax_use', '=', 'sale')])
                            data.append((0, 0, {'invoice_id': facture_line_retention.id, 'is_retention_client': True,
                                                'name': 'Retención IVA Cliente', 'tax_line': tax_id.amount, 'facture_amount': tax[2],
                                                'iva_amount': tax[1]}))
                if len(data) != 0:
                    return {'value': {'retention_line': data}}
                else:
                    raise exceptions.UserError(
                        "Disculpe, este cliente no tiene facturas registradas al que registrar retenciones")
            else:
                raise exceptions.UserError("Disculpe, este cliente es ordinario y no se le pueden aplicar retenciones")
        else:
            return
    
        """elif self.type == 'in_invoice' and self.partner_id:  # Rentention of Provider
            for facture_without_retention in self.env['account.invoice'].search(
                    [('origin', '=', False), ('partner_id', '=', self.partner_id.id),
                     ('type', 'in', ['in_invoice', 'in_debit'])]):
                if not facture_without_retention.apply_retention_iva and facture_without_retention.amount_tax > 0 and facture_without_retention.state == 'open':
                    data.append((0, 0, {'invoice_id': facture_without_retention.id, 'is_retention_client': False,
                                        'name': 'Retención Proveedor'}))
            return {'value': {'retention_line': data}}
    
        elif self.type == 'out_refund' and self.partner_id:  # Refund of client
            for facture_without_retention in self.env['account.invoice'].search(
                    [('origin', '!=', False), ('type', '=', 'out_refund'), ('partner_id', '=', self.partner_id.id)]):
                if not facture_without_retention.apply_retention_iva and facture_without_retention.amount_tax > 0:
                    data.append((0, 0, {'invoice_id': facture_without_retention.id, 'is_retention_client': True,
                                        'name': 'Reembolso de clientes'}))
            if len(data) != 0:
                return {'value': {'retention_line': data}}
            else:
                raise exceptions.UserError(
                    "Disculpe, este cliente no tiene facturas registradas al que registrar retenciones")
    
        elif self.type == 'in_refund' and self.partner_id:
            for facture_without_retention in self.env['account.invoice'].search(
                    [('partner_id', '=', self.partner_id.id),
                     ('type', '=', 'in_refund')]):
                if not facture_without_retention.apply_retention_iva and facture_without_retention.amount_tax > 0 and facture_without_retention.state == 'open':
                    data.append((0, 0, {'invoice_id': facture_without_retention.id, 'is_retention_client': False,
                                        'name': 'Retención NC Proveedor'}))
            return {'value': {'retention_line': data}}
    
        elif self.type == 'out_debit' and self.partner_id:  # Debit of client
            for facture_without_retention in self.env['account.invoice'].search(
                    [('type', '=', 'out_debit'), ('partner_id', '=', self.partner_id.id)]):
                if not facture_without_retention.apply_retention_iva and facture_without_retention.amount_tax > 0:
                    data.append((0, 0, {'invoice_id': facture_without_retention.id, 'is_retention_client': True,
                                        'name': 'Débito de clientes'}))
            if len(data) != 0:
                return {'value': {'retention_line': data}}
            else:
                raise exceptions.UserError(
                    "Disculpe, este cliente no tiene notas de débito registradas al que registrar retenciones")
    
        elif self.type == 'out_contingence' and self.partner_id:  # Contingence of client
            for facture_without_retention in self.env['account.invoice'].search(
                    [('type', '=', 'out_contingence'), ('partner_id', '=', self.partner_id.id),
                     ('state', 'in', ['open'])]):
                if not facture_without_retention.apply_retention_iva and facture_without_retention.amount_tax > 0:
                    data.append((0, 0, {'invoice_id': facture_without_retention.id, 'is_retention_client': True,
                                        'name': 'Contingencia de clientes'}))
            if len(data) != 0:
                return {'value': {'retention_line': data}}
            else:
                raise exceptions.UserError(
                    "Disculpe, este cliente no tiene facturas de contingencia registradas al que registrar retenciones")"""

    @api.depends('retention_line')
    def amount_ret_all(self):
        self.amount_base_ret = self.amount_imp_ret = self.total_tax_ret = self.amount_total_facture = self.amount_imp_ret = self.total_tax_ret = 0
        for line in self.retention_line:
            if not line.is_retention_client:
                self.amount_base_ret += line.base_ret
                self.amount_imp_ret += line.imp_ret
                self.total_tax_ret += line.amount_tax_ret
            else:
                self.amount_total_facture += line.facture_amount
                self.amount_imp_ret += line.iva_amount
                self.total_tax_ret += line.retention_amount

    @api.multi
    def action_emitted(self):
        today = datetime.datetime.now()
        if not self.date_accounting:
            self.date_accounting = str(today)
        if not self.date:
            self.date = str(today)
        if self.type in ['in_invoice', 'in_refund', 'in_debit']:
            #REVISAR CUANDO TOQUE EL FLUJO
            sequence = self.sequence()
            self.correlative = sequence.next_by_code('retention.iva.control.number')
            today = datetime.datetime.now()
            self.number = str(today.year) + today.strftime("%m") + self.correlative
            self.make_accounting_entries(False)
        elif self.type in ['out_invoice', 'out_refund', 'out_debit', 'out_contingence']:
            if not self.number:
                raise exceptions.UserError("Introduce el número de comprobante")
            self.make_accounting_entries(False)
        return self.write({'state': 'emitted'})

    name = fields.Char('Descripción', size=64, select=True, states={'draft': [('readonly', False)]},
                       help="Descripción del Comprobante")
    code = fields.Char('Código', size=32, states={'draft': [('readonly', False)]}, help="Referencia del Comprobante")
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('emitted', 'Emitida'),
        ('cancel', 'Cancelada')
    ], 'Estatus', select=True, default='draft', help="Estatus del Comprobante")
    type = fields.Selection([
        ('out_invoice', 'Factura de cliente'),
        ('in_invoice', 'Factura de proveedor'),
        ('out_refund', 'Nota de crédito de cliente'),
        ('in_refund', 'Nota de crédito de proveedor'),
        ('out_debit', 'Nota de débito de cliente'),
        ('in_debit', 'Nota de débito de proveedor'),
        ('out_contingence', 'Factura de contigencia de cliente'),
        ('in_contingence', 'Factura de contigencia de proveedor'),
    ], 'Tipo de retención', help="Tipo del Comprobante", required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', 'Razón Social', required=True,
                                 states={'draft': [('readonly', False)]},
                                 help="Proveedor o Cliente al cual se retiene o te retiene")
    currency_id = fields.Many2one('res.currency', 'Moneda', states={'draft': [('readonly', False)]},
                                  help="Moneda enla cual se realiza la operacion")
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env.user.company_id.id)
    number = fields.Char('Número de Comprobante')
    correlative = fields.Char(string='Nùmero correlativo', readonly=True)
    date = fields.Date('Fecha Comprobante', states={'draft': [('readonly', False)]},
                       help="Fecha de emision del comprobante de retencion por parte del ente externo.")
    date_accounting = fields.Date('Fecha Contable', states={'draft': [('readonly', False)]},
                                  help="Fecha de llegada del documento y fecha que se utilizara para hacer el registro contable.Mantener en blanco para usar la fecha actual.")

    retention_line = fields.One2many('account.retention.line', 'retention_id', 'Lineas de Retencion',
                                     states={'draft': [('readonly', False)]},
                                     help="Facturas a la cual se realizarán las retenciones")
    amount_base_ret = fields.Float(compute=amount_ret_all, string='Base Imponible', help="Total de la base retenida",
                                   store=True)
    amount_imp_ret = fields.Float(compute=amount_ret_all, store=True, string='Total IVA')
    total_tax_ret = fields.Float(compute=amount_ret_all, store=True, string='IVA retenido',
                                 help="Total del impuesto Retenido")

    amount_total_facture = fields.Float(compute=amount_ret_all, store=True, string="Total Facturado")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency")


class AccountRetentionBinauralLineFacturacion(models.Model):
    _name = 'account.retention.line'
    _rec_name = 'name'

    """@api.depends('invoice_id')
    def _amount_all(self):
        self.facture_amount = 0.00
        self.iva_amount = 0.00
        self.base_ret = 0.00
        self.imp_ret = 0.00
        self.amount_tax_ret = 0.00
        for record in self:
            if record.invoice_id:
                if record.invoice_id.move_type == 'out_invoice' or record.invoice_id.move_type == 'out_refund' or record.invoice_id.move_type == 'out_debit' or record.invoice_id.move_type == 'out_contingence':  # Cliente
                    record.facture_amount += self.invoice_id.amount_total
                    record.iva_amount += self.invoice_id.amount_tax
                elif record.invoice_id.move_type == 'in_invoice' or record.invoice_id.move_type == 'in_refund' or record.invoice_id.move_type == 'in_debit':  # Proveedor
                    record.base_ret = record.invoice_id.amount_untaxed
                    record.imp_ret = record.invoice_id.amount_tax
                    record.amount_tax_ret = record.imp_ret * record.retention_rate / 100"""

    @api.depends('invoice_id')
    def _retention_rate(self):
        if self.invoice_id.move_type in ['in_invoice', 'in_refund', 'in_debit']:
            self.retention_rate = self.invoice_id.partner_id.withholding_type.value

    @api.onchange('retention_amount')
    def _onchange_retention_amount(self):
        if self.retention_amount > self.iva_amount:
            return {
                'warning': {
                    'title': 'El monto retenido excedende',
                    'message': 'El monto a retener no debe superar al IVA de la factura, por favor verificar'
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
    reference_invoice_number = fields.Char(string="Número de factura", related="invoice_id.name", store=True)
    tax_line = fields.Float(string='Alicuota')
    amount_tax_ret = fields.Float(string='Impuesto retenido',
                                  help="Total impuesto retenido de la factura")
    base_ret = fields.Float(string='Base imponible',
                            help="Base retenida de la factura")
    imp_ret = fields.Float(string='Impuesto Causado')
    retention_rate = fields.Float(compute=_retention_rate, store=True, string='Portancentaje de Retención',
                                  help="Porcentaje de Retencion ha aplicar a la factura")

    is_retention_client = fields.Boolean(string='registro de retencion de cliente', default=True)
    display_invoice_number = fields.Char(string='Display', compute='_compute_fields_combination_iva', store=True)
    
    facture_amount = fields.Float(string='Monto total del documento')
    iva_amount = fields.Float(string='Iva factura')
    retention_amount = fields.Float(string='Monto Retenido')