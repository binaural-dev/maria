from odoo import api, fields, models, _, exceptions
from datetime import datetime

from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import math
import logging
_logger = logging.getLogger(__name__)


def load_line_retention(self, data, move_id=False):
    #CLIENTE
    if self.type in ['out_invoice']:
        for facture_line_retention in self.env['account.move'].search(
                [('partner_id', '=', self.partner_id.id), ('move_type', 'in', ['out_invoice', 'out_debit', 'out_refund']),
                 ('state', '=', 'posted'), ('journal_id.fiscal', '=', True)]):
            if self.type_retention in ['iva']:
                if not facture_line_retention.apply_retention_iva and facture_line_retention.amount_tax > 0\
                        and facture_line_retention.payment_state in ['not_paid', 'partial']:
                    for tax in facture_line_retention.amount_by_group:
                        _logger.info('TAXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                        _logger.info(tax)
                        tax_id = self.env['account.tax'].search([('tax_group_id', '=', tax[6]), ('type_tax_use', '=', 'sale')])
                        if tax_id.amount > 0:
                            data.append((0, 0, {'invoice_id': facture_line_retention.id, 'is_retention_client': True,
                                                'name': 'Retención IVA Cliente', 'tax_line': tax_id.amount,
                                                'facture_amount': tax[2],
                                                'facture_total': facture_line_retention.amount_total,
                                                'iva_amount': tax[1], 'invoice_type': facture_line_retention.move_type,
                                                'foreign_facture_amount': tax[2] * facture_line_retention.foreign_currency_rate,
                                                'foreign_facture_total': facture_line_retention.amount_total * facture_line_retention.foreign_currency_rate,
                                                'foreign_iva_amount': tax[1] * facture_line_retention.foreign_currency_rate,
                                                'foreign_currency_rate': facture_line_retention.foreign_currency_rate
                                                }))
            elif self.type_retention in ['islr']:
                if not facture_line_retention.apply_retention_islr and facture_line_retention.payment_state in ['not_paid', 'partial']:
                    data.append((0, 0, {'invoice_id': facture_line_retention.id, 'is_retention_client': True,
                                        'name': 'Retención ISLR Cliente',
                                        'facture_amount': facture_line_retention.amount_untaxed, 'facture_total': facture_line_retention.amount_total,
                                        'iva_amount': facture_line_retention.amount_tax, 'invoice_type': facture_line_retention.move_type,
                                        'foreign_facture_amount':facture_line_retention.amount_untaxed * facture_line_retention.foreign_currency_rate,
                                        'foreign_facture_total': facture_line_retention.amount_total * facture_line_retention.foreign_currency_rate,
                                        'foreign_iva_amount': facture_line_retention.amount_tax * facture_line_retention.foreign_currency_rate,
                                        'foreign_currency_rate': facture_line_retention.foreign_currency_rate
                                        }))
    #PROVEEDOR
    else:
        if self.type in ['in_invoice']:
            if move_id:
                invoices = self.env['account.move'].search(
                    [('partner_id', '=', self.partner_id.id),
                     ('move_type', 'in', ['in_invoice', 'in_debit', 'in_refund']),
                     ('state', '=', 'posted'), ('id', '=', move_id), ('journal_id.fiscal', '=', True)])
            else:
                invoices = self.env['account.move'].search(
                    [('partner_id', '=', self.partner_id.id),
                     ('move_type', 'in', ['in_invoice', 'in_debit', 'in_refund']),
                     ('state', '=', 'posted'), ('journal_id.fiscal', '=', True)])
            for facture_line_retention in invoices:
                if self.type_retention in ['iva']:
                    if not facture_line_retention.apply_retention_iva and facture_line_retention.amount_tax > 0 \
                            and facture_line_retention.payment_state in ['not_paid', 'partial']:
                        for tax in facture_line_retention.amount_by_group:
                            tax_id = self.env['account.tax'].search(
                                [('tax_group_id', '=', tax[6]), ('type_tax_use', '=', 'purchase')])
                            if tax_id.amount > 0:
                                data.append(
                                    (0, 0, {'invoice_id': facture_line_retention.id, 'is_retention_client': True,
                                            'name': 'Retención IVA Proveedor', 'tax_line': tax_id.amount,
                                            'facture_amount': tax[2],
                                            'facture_total': facture_line_retention.amount_total,
                                            'iva_amount': tax[1], 'invoice_type': facture_line_retention.move_type,
                                            'porcentage_retention': facture_line_retention.partner_id.withholding_type.value,
                                            'retention_amount': tax[1] * (facture_line_retention.partner_id.withholding_type.value/100),
                                            'foreign_facture_amount': tax[2] * facture_line_retention.foreign_currency_rate,
                                            'foreign_facture_total': facture_line_retention.amount_total * facture_line_retention.foreign_currency_rate,
                                            'foreign_iva_amount': tax[1] * facture_line_retention.foreign_currency_rate,
                                            'foreign_retention_amount': tax[1] * (facture_line_retention.partner_id.withholding_type.value/100) * facture_line_retention.foreign_currency_rate,
                                            'foreign_currency_rate': facture_line_retention.foreign_currency_rate
                                            }))
                                """elif self.type_retention in ['islr']:
        if not facture_line_retention.apply_retention_islr and facture_line_retention.payment_state in [\
                'not_paid', 'partial']:
            data.append((0, 0, {'invoice_id': facture_line_retention.id, 'is_retention_client': True,
                                'name': 'Retención ISLR Proveedor',
                                'facture_amount': facture_line_retention.amount_untaxed,
                                'facture_total': facture_line_retention.amount_total,
                                'iva_amount': facture_line_retention.amount_tax,
                                'invoice_type': facture_line_retention.move_type,
                                'porcentage_retention': facture_line_retention.partner_id.withholding_type.value,
                                'retention_amount': facture_line_retention.amount_tax * (
                                            facture_line_retention.partner_id.withholding_type.value / 100),
                                }))"""
        
    return data


def search_account(self, ret_line):
    # Verifica la cuenta por cobrar de la factura a utilizar en el asiento
    if self.type in ['out_invoice']:
        cxc = False
        for cta in ret_line.invoice_id.line_ids:
            if cta.account_id.user_type_id.type == 'receivable':
                cxc = cta.account_id.id
                return cxc
        if not cxc:
            raise UserError(
                "Disculpe, la factura %s no tiene ninguna cuenta por cobrar ") % ret_line.invoice_id.name
    else:
        cxp = False
        for cta in ret_line.invoice_id.line_ids:
            if cta.account_id.user_type_id.type == 'payable':
                cxp = cta.account_id.id
                return cxp
        if not cxp:
            raise UserError(
                "Disculpe, la factura %s no tiene ninguna cuenta por pagar ") % ret_line.invoice_id.name
        
    
def create_move_invoice_retention(self, line_ret, ret_line, account, journal, amount_edit, decimal_places, new_move, move_id):
    if self.type in ['out_invoice']:
        line_ret.append((0, 0, {
            'name': 'Cuentas por Cobrar Cientes (R)',
            'account_id': account,
            'partner_id': self.partner_id.id,
            'debit': 0,
            'credit': self.round_half_up(amount_edit,
                                         decimal_places) if amount_edit else self.round_half_up(
                ret_line.retention_amount, decimal_places),
        }))
        line_ret.append((0, 0, {
            'name': 'RC-' + self.number + "-" + ret_line.invoice_id.name,
            'account_id': self.partner_id.iva_retention.id if self.type_retention in ['iva'] else self.partner_id.islr_retention.id,
            'partner_id': self.partner_id.id,
            'debit': self.round_half_up(amount_edit,
                                        decimal_places) if amount_edit else self.round_half_up(
                ret_line.retention_amount, decimal_places),
            'credit': 0,
        }))
        # Asiento Contable
        if new_move:
            move_obj = self.env['account.move'].create({
                'name': 'RIV-' + self.number + "-" + ret_line.invoice_id.name if self.type_retention in ['iva'] else 'RIS-' + self.number + "-" + ret_line.invoice_id.name,
                'date': self.date_accounting,
                'journal_id': journal.id,
                'state': 'draft',
                'move_type': 'entry',
                'line_ids': line_ret,
                'foreign_currency_id': ret_line.invoice_id.foreign_currency_id.id,
                'foreign_currency_date': ret_line.invoice_id.foreign_currency_date,
                'foreign_currency_rate': ret_line.invoice_id.foreign_currency_rate
            })
            return move_obj
        else:
            move = self.env['account.move'].search(
                [('id', '=', move_id)])
            move.write({'line_ids': line_ret})
    else:
        if self.type_retention in ['iva']:
            cta_conf_supplier = int(self.env['ir.config_parameter'].sudo().get_param('account_retention_iva'))
        else:
            cta_conf_supplier = int(self.env['ir.config_parameter'].sudo().get_param('account_retention_islr'))
        cta_conf_supplier_id = self.env['account.account'].search([('id', '=', cta_conf_supplier)], limit=1)
        _logger.info('CUENTA DE CONFIGURACION DE IVA PROVEEDOR')
        _logger.info(cta_conf_supplier_id.id)
        _logger.info('CUENTA')
        _logger.info(account)
        line_ret.append((0, 0, {
            'name': 'Cuentas por Pagar Proveedores (R.IVA)',
            'account_id': account,
            'partner_id': self.partner_id.id,
            'debit': self.round_half_up(amount_edit,
                                         decimal_places) if amount_edit else self.round_half_up(
                ret_line.retention_amount, decimal_places),
            'credit': 0,
        }))
        line_ret.append((0, 0, {
            'name': 'RC-' + self.number + "-" + ret_line.invoice_id.name,
            'account_id': cta_conf_supplier_id.id,
            'partner_id': self.partner_id.id,
            'debit': 0,
            'credit': self.round_half_up(amount_edit,
                                        decimal_places) if amount_edit else self.round_half_up(
                ret_line.retention_amount, decimal_places),
        }))
        # Asiento Contable
        if new_move:
            move_obj = self.env['account.move'].create({
                'name': 'RIV-' + self.number + "-" + ret_line.invoice_id.name if self.type_retention in [
                    'iva'] else 'RIS-' + self.number + "-" + ret_line.invoice_id.name,
                'date': self.date_accounting,
                'journal_id': journal.id,
                'state': 'draft',
                'move_type': 'entry',
                'line_ids': line_ret,
                'foreign_currency_id': ret_line.invoice_id.foreign_currency_id.id,
                'foreign_currency_date': ret_line.invoice_id.foreign_currency_date,
                'foreign_currency_rate': ret_line.invoice_id.foreign_currency_rate
            })
            return move_obj
        else:
            move = self.env['account.move'].search(
                [('id', '=', move_id)])
            move.write({'line_ids': line_ret})
            
            
def create_move_refund_retention(self, line_ret, ret_line, account, journal, amount_edit, decimal_places, new_move, move_id):
    if self.type in ['out_invoice']:
        line_ret.append((0, 0, {
            'name': 'Cuentas por Cobrar Cientes (R)',
            'account_id': account,
            # account.id, Cuentas Por Cobrar Clientes
            'partner_id': self.partner_id.id,
            'debit': self.round_half_up(amount_edit,
                                        decimal_places) if amount_edit else self.round_half_up(
                ret_line.retention_amount, decimal_places),
            'credit': 0,
            'move_id': move_id
        }))
        line_ret.append((0, 0, {
            'name': 'RC-' + self.number + "-" + ret_line.invoice_id.name,
            'account_id': self.partner_id.iva_retention.id if self.type_retention in ['iva'] else self.partner_id.islr_retention.id,
            'partner_id': self.partner_id.id,
            'debit': 0,
            'credit': self.round_half_up(amount_edit,
                                         decimal_places) if amount_edit else self.round_half_up(
                ret_line.retention_amount, decimal_places),
            'move_id': move_id
        }))
        # Asiento Contable
        if new_move:
            move_obj = self.env['account.move'].create({
                'name': 'RIV-' + self.number + "-" + ret_line.invoice_id.name if self.type_retention in ['iva'] else 'RIS-' + self.number + "-" + ret_line.invoice_id.name,
                'date': self.date_accounting,
                'journal_id': journal.id,
                'state': 'draft',
                'move_type': 'entry',
                'line_ids': line_ret,
                'foreign_currency_id': ret_line.invoice_id.foreign_currency_id.id,
                'foreign_currency_date': ret_line.invoice_id.foreign_currency_date,
                'foreign_currency_rate': ret_line.invoice_id.foreign_currency_rate
            })
            return move_obj
        else:
            self.env['account.move.line'].create(line_ret)
    else:
        if self.type in ['iva']:
            cta_conf_supplier = int(self.env['ir.config_parameter'].sudo().get_param('account_retention_iva'))
        else:
            cta_conf_supplier = int(self.env['ir.config_parameter'].sudo().get_param('account_retention_islr'))
        cta_conf_supplier_id = self.env['account.account'].search([('id', '=', cta_conf_supplier)], limit=1)
        line_ret.append((0, 0, {
            'name': 'Cuentas por Pagar Proveedores (R.IVA)',
            'account_id': account,
            'partner_id': self.partner_id.id,
            'debit': 0,
            'credit': self.round_half_up(amount_edit,
                                        decimal_places) if amount_edit else self.round_half_up(
                ret_line.retention_amount, decimal_places),
        }))
        line_ret.append((0, 0, {
            'name': 'RC-' + self.number + "-" + ret_line.invoice_id.name,
            'account_id': cta_conf_supplier_id.id,
            'partner_id': self.partner_id.id,
            'debit': self.round_half_up(amount_edit,
                                         decimal_places) if amount_edit else self.round_half_up(
                ret_line.retention_amount, decimal_places),
            'credit': 0,
        }))
        # Asiento Contable
        if new_move:
            move_obj = self.env['account.move'].create({
                'name': 'RIV-' + self.number + "-" + ret_line.invoice_id.name if self.type_retention in [
                    'iva'] else 'RIS-' + self.number + "-" + ret_line.invoice_id.name,
                'date': self.date_accounting,
                'journal_id': journal.id,
                'state': 'draft',
                'move_type': 'entry',
                'line_ids': line_ret,
                'foreign_currency_id': ret_line.invoice_id.foreign_currency_id.id,
                'foreign_currency_date': ret_line.invoice_id.foreign_currency_date,
                'foreign_currency_rate': ret_line.invoice_id.foreign_currency_rate
            })
            return move_obj
        else:
            move = self.env['account.move'].search(
                [('id', '=', move_id)])
            move.write({'line_ids': line_ret})
