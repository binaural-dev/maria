from odoo import api, fields, models, _, exceptions
from datetime import datetime

from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import math
import logging
_logger = logging.getLogger(__name__)


def load_line_retention(self, data):
    for facture_line_retention in self.env['account.move'].search(
            [('partner_id', '=', self.partner_id.id), ('move_type', 'in', ['out_invoice', 'out_debit', 'out_refund']),
             ('state', '=', 'posted')]):
        if self.type_retention in ['iva']:
            if not facture_line_retention.apply_retention_iva and facture_line_retention.amount_tax > 0\
                    and facture_line_retention.payment_state in ['not_paid', 'partial']:
                for tax in facture_line_retention.amount_by_group:
                    tax_id = self.env['account.tax'].search([('tax_group_id', '=', tax[6]), ('type_tax_use', '=', 'sale')])
                    if tax_id.amount > 0:
                        data.append((0, 0, {'invoice_id': facture_line_retention.id, 'is_retention_client': True,
                                            'name': 'Retención IVA Cliente', 'tax_line': tax_id.amount,
                                            'facture_amount': tax[2],
                                            'iva_amount': tax[1], 'invoice_type': facture_line_retention.move_type}))
        elif self.type_retention in ['islr']:
            if not facture_line_retention.apply_retention_islr and facture_line_retention.payment_state in ['not_paid', 'partial']:
                data.append((0, 0, {'invoice_id': facture_line_retention.id, 'is_retention_client': True,
                                    'name': 'Retención ISLR Cliente',
                                    'facture_amount': facture_line_retention.amount_untaxed, 'facture_total': facture_line_retention.amount_total,
                                    'iva_amount': facture_line_retention.amount_tax, 'invoice_type': facture_line_retention.move_type}))
    return data


def search_account(ret_line):
    # Verifica la cuenta por cobrar de la factura a utilizar en el asiento
    cxc = False
    for cta in ret_line.invoice_id.line_ids:
        if cta.account_id.user_type_id.type == 'receivable':
            cxc = cta.account_id.id
            return cxc
    if not cxc:
        raise UserError(
            "Disculpe, la factura %s no tiene ninguna cuenta por cobrar ") % ret_line.invoice_id.name
    
    
def create_move_invoice_retention(self, line_ret, ret_line,cxc, journal_sale, amount_edit, decimal_places, new_move, move_id):
    line_ret.append((0, 0, {
        'name': 'Cuentas por Cobrar Cientes (R)',
        'account_id': cxc,
        'partner_id': self.partner_id.id,
        'debit': 0,
        'credit': self.round_half_up(amount_edit,
                                     decimal_places) if amount_edit else self.round_half_up(
            ret_line.retention_amount, decimal_places),
        'move_id': move_id
    }))
    line_ret.append((0, 0, {
        'name': 'RC-' + self.number + "-" + ret_line.invoice_id.name,
        'account_id': self.partner_id.iva_retention.id if self.type_retention in ['iva'] else self.partner_id.islr_retention.id,
        'partner_id': self.partner_id.id,
        'debit': self.round_half_up(amount_edit,
                                    decimal_places) if amount_edit else self.round_half_up(
            ret_line.retention_amount, decimal_places),
        'credit': 0,
        'move_id': move_id
    }))
    # Asiento Contable
    if new_move:
        move_obj = self.env['account.move'].create({
            'name': 'RIV-' + self.number + "-" + ret_line.invoice_id.name if self.type_retention in ['iva'] else 'RIS-' + self.number + "-" + ret_line.invoice_id.name,
            'date': self.date_accounting,
            'journal_id': journal_sale.id,
            'state': 'draft',
            'move_type': 'entry',
            'line_ids': line_ret
        })
        return move_obj
    else:
        self.env['account.move.line'].create(line_ret)


def create_move_refund_retention(self, line_ret, ret_line,cxc, journal_sale, amount_edit, decimal_places, new_move, move_id):
    line_ret.append((0, 0, {
        'name': 'Cuentas por Cobrar Cientes (R)',
        'account_id': cxc,
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
            'journal_id': journal_sale.id,
            'state': 'draft',
            'move_type': 'entry',
            'line_ids': line_ret
        })
        return move_obj
    else:
        self.env['account.move.line'].create(line_ret)
