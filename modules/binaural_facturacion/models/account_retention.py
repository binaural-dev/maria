from odoo import api, fields, models, _, exceptions
from datetime import datetime

from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import math
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
from .. models import funtions_retention

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

    def sequence_iva_retention(self):
        sequence = self.env['ir.sequence'].search([('code', '=', 'retention.iva.control.number')])
        if not sequence:
            sequence = self.env['ir.sequence'].create({
                'name': 'Numero de control',
                'code': 'retention.iva.control.number',
                'padding': 5
            })
        return sequence
    
    def sequence_islr_retention(self):
        sequence = self.env['ir.sequence'].search([('code', '=', 'retention.islr.control.number')])
        if not sequence:
            sequence = self.env['ir.sequence'].create({
                'name': 'Numero de control',
                'code': 'retention.islr.control.number',
                'padding': 5
            })
        return sequence

    @api.onchange('partner_id')
    def partner_id_onchange(self):
        data = []
        self.retention_line = False
        if self.type in ['out_invoice', 'in_invoice'] and self.partner_id:  # Rentention of client
            if self.partner_id.taxpayer != 'ordinary' or self.type in ['in_invoice']:
                funtions_retention.load_line_retention(self, data)
                if len(data) != 0:
                    return {'value': {'retention_line': data}}
                else:
                    if self.type in ['out_invoice']:
                        raise exceptions.UserError(
                            "Disculpe, este cliente no tiene facturas registradas al que registrar retenciones")
                    elif self.type_retention in ['iva']:
                        raise exceptions.UserError(
                            "Disculpe, este proveedor no tiene facturas registradas al que registrar retenciones")
            else:
                if self.type in ['out_invoice']:
                    raise exceptions.UserError("Disculpe, este cliente es ordinario y no se le pueden aplicar retenciones")
                else:
                    raise exceptions.UserError(
                        "Disculpe, este proveedor es ordinario y no se le pueden aplicar retenciones")
        else:
            return

    @api.depends('retention_line')
    def amount_ret_all(self):
        for record in self:
            record.amount_base_ret = record.amount_imp_ret = record.total_tax_ret = record.amount_total_facture = record.amount_imp_ret = record.total_tax_ret = 0
            invoices = []
            for line in record.retention_line:
                if not line.is_retention_client:
                    record.amount_base_ret += line.base_ret
                    record.amount_imp_ret += line.imp_ret
                    record.total_tax_ret += line.amount_tax_ret

                    record.foreign_amount_base_ret += line.foreign_base_ret
                    record.foreign_amount_imp_ret += line.foreign_imp_ret
                    record.foreign_total_tax_ret += line.foreign_amount_tax_ret
                else:
                    total_sum = 0
                    foreign_total_sum = 0
                    if line.invoice_id.id not in invoices:
                        total_sum = line.invoice_id.amount_total
                        foreign_total_sum = line.invoice_id.foreign_amount_total
                        invoices.append(line.invoice_id.id)
                    if line.invoice_type in ['out_invoice', 'out_debit', 'in_invoice', 'in_debit']:
                        _logger.info('tipo de factura')
                        _logger.info(line.invoice_type)
                        record.amount_total_facture += total_sum
                        record.amount_imp_ret += line.iva_amount
                        record.total_tax_ret += line.retention_amount

                        record.foreign_amount_total_facture += foreign_total_sum
                        record.foreign_amount_imp_ret += line.foreign_iva_amount
                        record.foreign_total_tax_ret += line.foreign_retention_amount
                    elif line.invoice_type in ['out_refund', 'in_refund']:
                        _logger.info('tipo de factura1')
                        _logger.info(line.invoice_type)
                        record.amount_total_facture -= total_sum
                        record.amount_imp_ret -= line.iva_amount
                        record.total_tax_ret -= line.retention_amount

                        record.foreign_amount_total_facture -= foreign_total_sum
                        record.foreign_amount_imp_ret -= line.foreign_iva_amount
                        record.foreign_total_tax_ret -= line.foreign_retention_amount
                    else:
                        _logger.info('tipo de factura3')
                        _logger.info(line.invoice_type)

    def action_emitted(self):
        today = datetime.now()
        if not self.date_accounting:
            self.date_accounting = str(today)
        if not self.date:
            self.date = str(today)
        if self.type in ['in_invoice', 'in_refund', 'in_debit']:
            #REVISAR CUANDO TOQUE EL FLUJO
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
            if line.retention_id.type_retention in ['iva']:
                line.invoice_id.write({'apply_retention_iva': False, 'iva_voucher_number': None})
            if line.retention_id.type_retention in ['islr']:
                line.invoice_id.write({'apply_retention_islr': False, 'islr_voucher_number': None})
            #line.move_id.unlink()
        self.write({'state': 'cancel'})
        return True
    
    def retention_currency_system(self):
        self.write({'actual_currency_retention': False})
        
    def retention_foreign_currency(self):
        self.write({'actual_currency_retention': True})
    
    def action_draft(self):
        self.write({'state': 'draft'})
        return True
    
    def _check_group_multi_currency(self):
        for record in self:
            if self.env.user.has_group('binaural_facturacion.group_multi_currency_retention'):
                record.multi_currency_retention = True
            else:
                record.multi_currency_retention = False
                
    def default_alternate_currency(self):
        alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))

        if alternate_currency:
            return alternate_currency
        else:
            return False

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

    foreign_amount_base_ret = fields.Float(compute=amount_ret_all, string='Base Imponible', help="Total de la base retenida",
                                   store=True)
    foreign_amount_imp_ret = fields.Float(compute=amount_ret_all, store=True, string='Total IVA')
    foreign_total_tax_ret = fields.Float(compute=amount_ret_all, store=True, string='IVA retenido',
                                 help="Total del impuesto Retenido")
    foreign_amount_total_facture = fields.Float(compute=amount_ret_all, store=True, string="Total Facturado")

    amount_total_facture = fields.Float(compute=amount_ret_all, store=True, string="Total Facturado")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency")
    type_retention = fields.Selection([
        ('iva', 'IVA'),
        ('islr', 'ISLR'),
    ], 'Tipo de retención')
    multi_currency_retention = fields.Boolean(string='Retenciones multimoneda', compute='_check_group_multi_currency')
    actual_currency_retention = fields.Boolean(string='Retenciones en moneda alterna', default=False)

    foreign_currency_id = fields.Many2one('res.currency', default=default_alternate_currency,
                                          tracking=True)
    
    def round_half_up(self, n, decimals=0):
        multiplier = 10 ** decimals
        return math.floor(n * multiplier + 0.5) / multiplier

    def make_accounting_entries(self, amount_edit):
        move, facture, move_ids = [], [], []
        invoices = []
        decimal_places = self.company_id.currency_id.decimal_places
        journal_sale_id = int(self.env['ir.config_parameter'].sudo().get_param('journal_retention_client'))
        journal_sale = self.env['account.journal'].search([('id', '=', journal_sale_id)], limit=1)
        journal_purchase_id = int(self.env['ir.config_parameter'].sudo().get_param('journal_retention_supplier'))
        journal_purchase = self.env['account.journal'].search([('id', '=', journal_purchase_id)], limit=1)
        if not journal_sale and self.type_retention in ['out_invoice']:
            raise UserError("Por favor configure los diarios de las renteciones")
        if not journal_purchase and self.type_retention in ['in_invoice']:
            raise UserError("Por favor configure los diarios de las renteciones")
        if self.type == 'out_invoice':
            for ret_line in self.retention_line:
                line_ret = []
                if ret_line.retention_amount > 0:
                    if ret_line.invoice_id.name not in invoices:
                        # Crea los apuntes y asiento contable  de las primeras lineas de retencion
                        if self.round_half_up(ret_line.retention_amount, decimal_places) <= self.round_half_up(
                                ret_line.invoice_id.amount_tax, decimal_places) or self.type_retention in ['islr']:
                            cxc = funtions_retention.search_account(self, ret_line)
                            if ret_line.invoice_id.move_type not in ['out_refund']:
                                # Crea los apuntes contables para las facturas, Nota debito
                                # Apuntes
                                move_obj = funtions_retention.create_move_invoice_retention(self, line_ret, ret_line,
                                                                                            cxc, journal_sale, amount_edit,
                                                                                            decimal_places, True, False)
                                move_ids.append(move_obj.id)
                            else:
                                # Crea los apuntes contables para las notas de credito
                                # Apuntes
                                move_obj = funtions_retention.create_move_refund_retention(self, line_ret, ret_line,
                                                                                            cxc, journal_sale, amount_edit,
                                                                                            decimal_places, True, False)
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
                                ret_line.invoice_id.amount_tax, decimal_places) or self.type_retention in ['islr']:
                            # Verifica la cuenta por cobrar de la factura a utilizar en el asiento
                            cxc = funtions_retention.search_account(self, ret_line)
                            if ret_line.invoice_id.move_type not in ['out_refund']:
                                # Crea los apuntes contables para las facturas, Nota debito y lo asocia al asiento creado
                                # (Un solo movimiento por impuestos de factura)
                                # Apuntes
                                funtions_retention.create_move_invoice_retention(self, line_ret, ret_line,
                                                                                            cxc, journal_sale,
                                                                                            amount_edit,
                                                                                            decimal_places, False, move_obj.id)
                            else:
                                funtions_retention.create_move_refund_retention(self, line_ret, ret_line,
                                                                                            cxc, journal_sale,
                                                                                            amount_edit,
                                                                                            decimal_places, False, move_obj.id)
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
                if ret_line.retention_id.type_retention in ['iva']:
                    _logger.info('AGREGAR NUMERO DE COMPPOBANTE DE IVA A FACTURA ')
                    _logger.info(ret_line.invoice_id.name)
                    _logger.info(ret_line.retention_id.number)
                    ret_line.invoice_id.write(
                        {'apply_retention_iva': True, 'iva_voucher_number': ret_line.retention_id.number})
                elif ret_line.retention_id.type_retention in ['islr']:
                    _logger.info('AGREGAR NUMERO DE COMPPOBANTE DE ISLR A FACTURA ')
                    _logger.info(ret_line.invoice_id.name)
                    _logger.info(ret_line.retention_id.number)
                    ret_line.invoice_id.write(
                        {'apply_retention_islr': True, 'islr_voucher_number': ret_line.retention_id.number})
                
            moves = self.env['account.move.line'].search(
                [('move_id', 'in', move_ids), ('name', '=', 'Cuentas por Cobrar Cientes (R)')])
            for mv in moves:
                move.append(mv)
            for rlines in self.retention_line:
                if rlines.move_id and rlines.move_id.state in 'draft':
                    rlines.move_id.action_post()
            for index, move_line in enumerate(move):
                facture[index].js_assign_outstanding_line(move_line.id)
        else:
            for ret_line in self.retention_line:
                line_ret = []
                if ret_line.retention_amount > 0:
                    if ret_line.invoice_id.name not in invoices:
                        _logger.info('CREO EL MOVIMIENTOOOOOOOOOOOOOOOOOOOOOOO')
                        # Crea los apuntes y asiento contable  de las primeras lineas de retencion
                        if self.round_half_up(ret_line.retention_amount, decimal_places) <= self.round_half_up(
                                ret_line.invoice_id.amount_tax, decimal_places) or self.type_retention in ['islr']:
                            cxp = funtions_retention.search_account(self, ret_line)
                            if cxp and journal_purchase:
                                if self.type_retention in ['iva']:
                                    sequence = self.sequence_iva_retention()
                                    correlative = sequence.next_by_code('retention.iva.control.number')
                                else:
                                    sequence = self.sequence_islr_retention()
                                    correlative = sequence.next_by_code('retention.islr.control.number')
                                today = datetime.now()                               
                                number = str(ret_line.invoice_id.date.year) + '{:02d}'.format(ret_line.invoice_id.date.month) + correlative
                                self.write({'correlative': correlative, 'number': number})
                            if ret_line.invoice_id.move_type not in ['in_refund']:
                                # Crea los apuntes contables para las facturas, Nota debito
                                # Apuntes
                                move_obj = funtions_retention.create_move_invoice_retention(self, line_ret, ret_line,
                                                                                            cxp, journal_purchase,
                                                                                            amount_edit,
                                                                                            decimal_places, True, False)
                                move_ids.append(move_obj.id)
                            else:
                                # Crea los apuntes contables para las notas de credito
                                # Apuntes
                                move_obj = funtions_retention.create_move_refund_retention(self, line_ret, ret_line,
                                                                                           cxp, journal_purchase,
                                                                                           amount_edit,
                                                                                           decimal_places, True, False)
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
                        _logger.info('CREO EL EL SEGUNDO LINEA EN EL MOVIMIENTOOOOOOOOOOOOOOOOOOOOOOO')
                        # Crea los apuntes contables y los asocia a el asiento contable creado para las primeras lineas de la retencion
                        if self.round_half_up(ret_line.retention_amount, decimal_places) <= self.round_half_up(
                                ret_line.invoice_id.amount_tax, decimal_places) or self.type_retention in ['islr']:
                            # Verifica la cuenta por cobrar de la factura a utilizar en el asiento
                            cxp = funtions_retention.search_account(self, ret_line)
                            if ret_line.invoice_id.move_type not in ['in_refund']:
                                # Crea los apuntes contables para las facturas, Nota debito y lo asocia al asiento creado
                                # (Un solo movimiento por impuestos de factura)
                                # Apuntes
                                funtions_retention.create_move_invoice_retention(self, line_ret, ret_line,
                                                                                 cxp, journal_purchase,
                                                                                 amount_edit,
                                                                                 decimal_places, False, move_obj.id)
                            else:
                                funtions_retention.create_move_refund_retention(self, line_ret, ret_line,
                                                                                cxp, journal_purchase,
                                                                                amount_edit,
                                                                                decimal_places, False, move_obj.id)
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
                if ret_line.retention_id.type_retention in ['iva']:
                    _logger.info('AGREGAR NUMERO DE COMPPOBANTE DE IVA A FACTURA ')
                    _logger.info(ret_line.invoice_id.name)
                    _logger.info(ret_line.retention_id.number)
                    ret_line.invoice_id.write(
                        {'apply_retention_iva': True, 'iva_voucher_number': ret_line.retention_id.number})
                elif ret_line.retention_id.type_retention in ['islr']:
                    _logger.info('AGREGAR NUMERO DE COMPPOBANTE DE ISLR A FACTURA ')
                    _logger.info(ret_line.invoice_id.name)
                    _logger.info(ret_line.retention_id.number)
                    ret_line.invoice_id.write(
                        {'apply_retention_islr': True, 'islr_voucher_number': ret_line.retention_id.number})
            moves = self.env['account.move.line'].search(
                [('move_id', 'in', move_ids), ('name', '=', 'Cuentas por Pagar Proveedores (R.IVA)')])
            for mv in moves:
                move.append(mv)
            for rlines in self.retention_line:
                if rlines.move_id and rlines.move_id.state in 'draft':
                    rlines.move_id.action_post()
            for index, move_line in enumerate(move):
                facture[index].js_assign_outstanding_line(move_line.id)