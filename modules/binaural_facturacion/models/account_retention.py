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
                        [('partner_id', '=', self.partner_id.id), ('move_type', 'in', ['out_invoice', 'out_debit', 'out_refund']),
                         ('state', '=', 'posted')]):
                    # 'move_id': move_obj.id,
                    if not facture_line_retention.apply_retention_iva and facture_line_retention.amount_tax > 0 and facture_line_retention.payment_state in ['not_paid', 'partial']:
                        for tax in facture_line_retention.amount_by_group:
                            tax_id = self.env['account.tax'].search([('tax_group_id', '=', tax[6]), ('type_tax_use', '=', 'sale')])
                            if tax_id.amount > 0:
                                data.append((0, 0, {'invoice_id': facture_line_retention.id, 'is_retention_client': True,
                                                    'name': 'Retención IVA Cliente', 'tax_line': tax_id.amount, 'facture_amount': tax[2],
                                                    'iva_amount': tax[1], 'invoice_type': facture_line_retention.move_type}))
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
                if line.invoice_type in ['out_invoice', 'out_debit', 'in_refund']:
                    self.amount_total_facture += line.facture_amount
                    self.amount_imp_ret += line.iva_amount
                    self.total_tax_ret += line.retention_amount
                else:
                    self.amount_total_facture -= line.facture_amount
                    self.amount_imp_ret -= line.iva_amount
                    self.total_tax_ret -= line.retention_amount

    def action_emitted(self):
        today = datetime.now()
        if not self.date_accounting:
            self.date_accounting = str(today)
        if not self.date:
            self.date = str(today)
        if self.type in ['in_invoice', 'in_refund', 'in_debit']:
            #REVISAR CUANDO TOQUE EL FLUJO
            sequence = self.sequence()
            self.correlative = sequence.next_by_code('retention.iva.control.number')
            today = datetime.now()
            self.number = str(today.year) + today.strftime("%m") + self.correlative
            self.make_accounting_entries(False)
        elif self.type in ['out_invoice', 'out_refund', 'out_debit']:
            if not self.number:
                raise exceptions.UserError("Introduce el número de comprobante")
            self.make_accounting_entries(False)
        return self.write({'state': 'emitted'})

    def action_cancel(self):
        for line in self.retention_line:
            if line.move_id and line.move_id.line_ids:
                line.move_id.line_ids.remove_move_reconcile()
            if line.move_id and line.move_id.state != 'draft':
                line.move_id.button_cancel()
            line.invoice_id.write({'apply_retention_iva': False, 'iva_voucher_number': None})
            #line.move_id.unlink()
        self.write({'state': 'cancel'})
        return True

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
    
    def round_half_up(self, n, decimals=0):
        multiplier = 10 ** decimals
        return math.floor(n * multiplier + 0.5) / multiplier

    def make_accounting_entries(self, amount_edit):
        move, facture, move_ids = [], [], []
        invoices = []
        decimal_places = self.company_id.currency_id.decimal_places
        journal_sale_id = int(self.env['ir.config_parameter'].sudo().get_param('journal_retention_client'))
        journal_sale = self.env['account.journal'].search([('id', '=', journal_sale_id)], limit=1)
        if not journal_sale:
            raise UserError("Por favor configure los diarios de las renteciones")
    
        if self.type == 'out_invoice':
            for ret_line in self.retention_line:
                line_ret = []
                if ret_line.retention_amount > 0:
                    if ret_line.invoice_id.name not in invoices:
                        # Crea los apuntes y asiento contable  de las primeras lineas de retencion
                        if self.round_half_up(ret_line.retention_amount, decimal_places) <= self.round_half_up(
                                ret_line.invoice_id.amount_tax, decimal_places):
                            # Verifica la cuenta por cobrar de la factura a utilizar en el asiento
                            cxc = False
                            for cta in ret_line.invoice_id.line_ids:
                                if cta.account_id.user_type_id.type == 'receivable':
                                    cxc = cta.account_id.id
                            if not cxc:
                                raise UserError(
                                    "Disculpe, la factura %s no tiene ninguna cuenta por cobrar ") % ret_line.invoice_id.name
                            if ret_line.invoice_id.move_type not in ['out_refund']:
                                # Crea los apuntes contables para las facturas, Nota debito
                                # Apuntes
                                line_ret.append((0, 0, {
                                    'name': 'Cuentas por Cobrar Cientes (R)',
                                    'account_id': cxc,
                                    'partner_id': self.partner_id.id,
                                    'debit': 0,
                                    'credit': self.round_half_up(amount_edit,
                                                                 decimal_places) if amount_edit else self.round_half_up(
                                        ret_line.retention_amount, decimal_places),
                                }))
                                line_ret.append((0, 0, {
                                    'name': 'RC-' + self.number + "-" + ret_line.invoice_id.name,
                                    'account_id': self.partner_id.iva_retention.id,  # Retencion de IVA
                                    'partner_id': self.partner_id.id,
                                    'debit': self.round_half_up(amount_edit,
                                                                decimal_places) if amount_edit else self.round_half_up(
                                        ret_line.retention_amount, decimal_places),
                                    'credit': 0,
                                }))
                                # Asiento Contable
                                move_obj = self.env['account.move'].create({
                                    'name': 'RIV-' + self.number + "-" + ret_line.invoice_id.name,
                                    'date': self.date_accounting,
                                    'journal_id': journal_sale.id,
                                    'state': 'draft',
                                    'move_type': 'entry',
                                    'line_ids': line_ret
                                })
                                move_ids.append(move_obj.id)
                            else:
                                # Crea los apuntes contables para las notas de credito
                                # Apuntes
                                line_ret.append((0, 0, {
                                    'name': 'Cuentas por Cobrar Cientes (R)',
                                    'account_id': cxc,
                                    # account.id, Cuentas Por Cobrar Clientes
                                    'partner_id': self.partner_id.id,
                                    'debit': self.round_half_up(amount_edit,
                                                                decimal_places) if amount_edit else self.round_half_up(
                                        ret_line.retention_amount, decimal_places),
                                    'credit': 0,
                                }))
                                line_ret.append((0, 0, {
                                    'name': 'RC-' + self.number + "-" + ret_line.invoice_id.name,
                                    'account_id': self.partner_id.iva_retention.id,  # Retencion de IVA
                                    'partner_id': self.partner_id.id,
                                    'debit': 0,
                                    'credit': self.round_half_up(amount_edit,
                                                                 decimal_places) if amount_edit else self.round_half_up(
                                        ret_line.retention_amount, decimal_places),
                                }))
                                # Asiento Contable
                                move_obj = self.env['account.move'].create({
                                    'name': 'RIV-' + self.number + "-" + ret_line.invoice_id.name,
                                    'date': self.date_accounting,
                                    'journal_id': journal_sale.id,
                                    'state': 'draft',
                                    'move_type': 'entry',
                                    'line_ids': line_ret
                                })
                                move_ids.append(move_obj.id)
                            # Va recopilando los IDS de las facturas para la conciliacion
                            facture.append(ret_line.invoice_id)
                            # Asocia el apunte al asiento contable creado
                            ret_line.move_id = move_obj.id
                        else:
                            raise UserError("Disculpe, el monto retenido de la factura " + str(
                                ret_line.invoice_id.name) + ' no debe superar la cantidad de IVA registrado')
                        invoices.append(ret_line.invoice_id.name)
                    else:
                        # Crea los apuntes contables y los asocia a el asiento contable creado para las primeras lineas de la retencion
                        if self.round_half_up(ret_line.retention_amount, decimal_places) <= self.round_half_up(
                                ret_line.invoice_id.amount_tax, decimal_places):
                            # Verifica la cuenta por cobrar de la factura a utilizar en el asiento
                            cxc = False
                            for cta in ret_line.invoice_id.line_ids:
                                if cta.account_id.user_type_id.type == 'receivable':
                                    cxc = cta.account_id.id
                            if not cxc:
                                raise UserError(
                                    "Disculpe, la factura %s no tiene ninguna cuenta por cobrar ") % ret_line.invoice_id.name
                            if ret_line.invoice_id.move_type not in ['out_refund']:
                                # Crea los apuntes contables para las facturas, Nota debito y lo asocia al asiento creado
                                # (Un solo movimiento por impuestos de factura)
                                # Apuntes
                                line_ret.append({
                                    'name': 'Cuentas por Cobrar Cientes (R)',
                                    'account_id': cxc,
                                    'partner_id': self.partner_id.id,
                                    'debit': 0,
                                    'credit': self.round_half_up(amount_edit,
                                                                 decimal_places) if amount_edit else self.round_half_up(
                                        ret_line.retention_amount, decimal_places),
                                    'move_id': move_obj.id,
                                })
                                line_ret.append({
                                    'name': 'RC-' + self.number + "-" + ret_line.invoice_id.name,
                                    'account_id': self.partner_id.iva_retention.id,  # Retencion de IVA
                                    'partner_id': self.partner_id.id,
                                    'debit': self.round_half_up(amount_edit,
                                                                decimal_places) if amount_edit else self.round_half_up(
                                        ret_line.retention_amount, decimal_places),
                                    'credit': 0,
                                    'move_id': move_obj.id,
                                })
                                self.env['account.move.line'].create(line_ret)
                            else:
                                line_ret.append({
                                    'name': 'Cuentas por Cobrar Cientes (R)',
                                    'account_id': cxc,
                                    'partner_id': self.partner_id.id,
                                    'debit': self.round_half_up(amount_edit,
                                                                decimal_places) if amount_edit else self.round_half_up(
                                        ret_line.retention_amount, decimal_places),
                                    'credit': 0,
                                    'move_id': move_obj.id,
                                })
                                line_ret.append({
                                    'name': 'RC-' + self.number + "-" + ret_line.invoice_id.name,
                                    'account_id': self.partner_id.iva_retention.id,  # Retencion de IVA
                                    'partner_id': self.partner_id.id,
                                    'debit': 0,
                                    'credit': self.round_half_up(amount_edit,
                                                                 decimal_places) if amount_edit else self.round_half_up(
                                        ret_line.retention_amount, decimal_places),
                                    'move_id': move_obj.id,
                                })
                                _logger.info('2DA LINEA DE RETENTION DE NC')
                                _logger.info(line_ret)
                                self.env['account.move.line'].create(line_ret)
                                # Crea los apuntes contables para las notas de credito y lo asocia al asiento contable
                                # Apuntes
                            facture.append(ret_line.invoice_id)
                            ret_line.move_id = move_obj.id
                        else:
                            raise UserError("Disculpe, el monto retenido de la factura " + str(
                                ret_line.invoice_id.name) + ' no debe superar la cantidad de IVA registrado')
                else:
                    raise UserError(
                        "Disculpe, la factura " + str(ret_line.invoice_id.name) + ' no posee el monto retenido')
            
                ret_line.invoice_id.write(
                    {'apply_retention_iva': True, 'iva_voucher_number': ret_line.retention_id.number})
            moves = self.env['account.move.line'].search(
                [('move_id', 'in', move_ids), ('name', '=', 'Cuentas por Cobrar Cientes (R)')])
            _logger.info('MOVES')
            _logger.info(moves)
            for mv in moves:
                move.append(mv)
            for rlines in self.retention_line:
                if rlines.move_id and rlines.move_id.state in 'draft':
                    rlines.move_id.action_post()
            for index, move_line in enumerate(move):
                facture[index].js_assign_outstanding_line(move_line.id)
        else:
            return


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