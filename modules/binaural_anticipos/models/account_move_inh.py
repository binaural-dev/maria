# -*- coding: utf-8 -*-

import logging
import time
from datetime import date
from collections import OrderedDict
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools.misc import formatLang, format_date
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
from odoo.addons import decimal_precision as dp
from lxml import etree
import json


_logger = logging.getLogger(__name__)


class account_payment_inh(models.Model):
    _inherit = 'account.move'
    
    outstanding_credits_debits_widget2 = fields.Text(compute='_get_outstanding_info_JSON2', groups="account.group_account_invoice")
    invoice_outstanding_credits_debits_widget2 = fields.Text(
        groups="account.group_account_invoice,account.group_account_readonly",
        compute='_compute_payments_widget_to_reconcile_info2')
    
    def cancel_move(self):
        self.button_draft()
        self.button_cancel()

    def _compute_payments_widget_to_reconcile_info2(self):
        for move in self:
            move.invoice_outstanding_credits_debits_widget2 = json.dumps(False)
            move.invoice_has_outstanding = False
        
            if move.state != 'posted' \
                    or move.payment_state not in ('not_paid', 'partial') \
                    or not move.is_invoice(include_receipts=True):
                continue
        
            pay_term_lines = move.line_ids \
                .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            domain=[]
            if move.move_type in ('out_invoice', 'in_refund'):
                _logger.info('1111111111111111111')
                advance_account = self.env['account.payment.config.advance'].search(
                    [('active', '=', True), ('advance_type', '=', 'customer')], limit=1)
                if advance_account:
                    domain = [
                        ('account_id', '=', advance_account.advance_account_id.id),
                        ('move_id.state', '=', 'posted'),
                        ('partner_id', '=', move.commercial_partner_id.id),
                        ('reconciled', '=', False),
                        '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
                        ('credit', '>', 0),
                        ('debit', '=', 0)
                    ]
                    _logger.info('ADVANCE_ACCOUNT')
                    _logger.info(advance_account)
            else:
                _logger.info('2222222222222222222222')
                advance_account = self.env['account.payment.config.advance'].search(
                    [('active', '=', True), ('advance_type', '=', 'supplier')], limit=1)
                if advance_account:
                    domain = [
                        ('account_id', '=', advance_account.advance_account_id.id),
                        ('move_id.state', '=', 'posted'),
                        ('partner_id', '=', move.commercial_partner_id.id),
                        ('reconciled', '=', False),
                        '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
                        ('credit', '=', 0),
                        ('debit', '>', 0)
                    ]
                    _logger.info('ADVANCE_ACCOUNT2')
                    _logger.info(advance_account)
            payments_widget_vals = {'outstanding': True, 'content': [], 'move_id': move.id}
        
            if move.is_inbound():
                domain.append(('balance', '<', 0.0))
                payments_widget_vals['title'] = _('Outstanding credits')
            else:
                domain.append(('balance', '>', 0.0))
                payments_widget_vals['title'] = _('Outstanding debits')
        
            _logger.info('DOMAIN')
            _logger.info(domain)
            for line in self.env['account.move.line'].search(domain):
                _logger.info('ID')
                _logger.info(line.id)
                if line.currency_id == move.currency_id:
                    # Same foreign currency.
                    amount = abs(line.amount_residual_currency)
                else:
                    # Different foreign currencies.
                    amount = move.company_currency_id._convert(
                        abs(line.amount_residual),
                        move.currency_id,
                        move.company_id,
                        line.date,
                    )
            
                if move.currency_id.is_zero(amount):
                    continue
            
                payments_widget_vals['content'].append({
                    'journal_name': line.ref or line.move_id.name,
                    'amount': amount,
                    'currency': move.currency_id.symbol,
                    'id': line.id,
                    'move_id': line.move_id.id,
                    'position': move.currency_id.position,
                    'digits': [69, move.currency_id.decimal_places],
                    'payment_date': fields.Date.to_string(line.date),
                })
        
            if not payments_widget_vals['content']:
                continue
        
            move.invoice_outstanding_credits_debits_widget2 = json.dumps(payments_widget_vals)
            move.invoice_has_outstanding = True

    def _get_outstanding_info_JSON2(self):
        self.outstanding_credits_debits_widget2 = json.dumps(False)
        if self.payment_state in ['not_paid', 'in_payment', 'partial']:
            domain = [('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                      ('move_id.state', '=', 'posted'),
                      '|',
                      '&', ('amount_residual_currency', '!=', 0.0), ('currency_id', '!=', None),
                      '&', ('amount_residual_currency', '=', 0.0), '&', ('currency_id', '=', None),
                      ('amount_residual', '!=', 0.0)]
            if self.move_type in ('out_invoice', 'in_refund'):
                print("es creditos")
                advance_account = self.env['account.payment.config.advance'].search(
                    [('active', '=', True), ('advance_type', '=', 'customer')], limit=1)
                if advance_account:
                    domain.extend([('account_id', '=', advance_account.advance_account_id.id)])
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                
                type_payment = _('Anticipos')
            else:
                print("es debitos")
                advance_account = self.env['account.payment.config.advance'].search(
                    [('active', '=', True), ('advance_type', '=', 'supplier')], limit=1)
                if advance_account:
                    domain.extend([('account_id', '=', advance_account.advance_account_id.id)])
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                type_payment = _('Anticipos')
            info = {'title': '', 'outstanding': True, 'content': [], 'invoice_id': self.id}
            if advance_account:
                lines = self.env['account.move.line'].search(domain)
            else:
                lines = []
            currency_id = self.currency_id
            if len(lines) != 0:
                for line in lines:
                    # get the outstanding residual value in invoice currency
                    if line.currency_id and line.currency_id == self.currency_id:
                        amount_to_show = abs(line.amount_residual_currency)
                    else:
                        currency = line.company_id.currency_id
                        amount_to_show = currency._convert(abs(line.amount_residual), self.currency_id, self.company_id,
                                                           line.date or fields.Date.today())
                    if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
                        continue
                    if line.ref:
                        title = '%s : %s' % (line.move_id.name, line.ref)
                    else:
                        title = line.move_id.name
                    info['content'].append({
                        'journal_name': line.ref or line.move_id.name,
                        'title': title,
                        'amount': amount_to_show,
                        'currency': currency_id.symbol,
                        'id': line.id,
                        'position': currency_id.position,
                        'digits': [69, self.currency_id.decimal_places],
                    })
                info['title'] = type_payment
                self.outstanding_credits_debits_widget2 = json.dumps(info)
                #self.has_outstanding = True

    def js_assign_outstanding_line(self, line_id):
        ''' Called by the 'payment' widget to reconcile a suggested journal item to the present
        invoice.

        :param line_id: The id of the line to reconcile with the current invoice.
        '''
        self.ensure_one()
        lines = self.env['account.move.line'].browse(line_id)
        payment = self.env['account.payment'].search(
            [('move_id', '=', lines.move_id.id)], limit=1)
        cta = False
        for c in self.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable') and not line.reconciled):
            cta = c.account_id.id
        if payment.is_advance:
            line_payment_advance = payment.move_id.line_ids.filtered(lambda line: line.account_id == payment.destination_account_id)
            min_amount = 0
            if -line_payment_advance[0].amount_residual < self.amount_residual:
                min_amount = -line_payment_advance[0].amount_residual
            else:
                min_amount = self.amount_residual
            if payment.currency_id and payment.currency_id == self.currency_id:
                amount = abs(min_amount)
                amount = self.currency_id.round(amount)
            else:
                currency = payment.company_id.currency_id
                amount = currency._convert(abs(min_amount), self.currency_id,
                                           self.company_id, payment.date or fields.Date.today())
                amount = currency.round(amount)
            if self.move_type in ['out_invoice', 'in_refund']:
                line_ret = [(0, 0, {
                    # tomar esta linea para reconciliar
                    'name': 'CUENTA POR COBRAR CLIENTE',
                    'account_id': cta,  # cuenta de la factura, CXC
                    'partner_id': self.partner_id.id,
                    'credit': amount,
                    'debit': 0,
                    'foreign_currency_rate': payment.foreign_currency_rate,
                    'payment_id_advance': payment.id,
                    'reconciled': False,
                }), (0, 0, {
                    'name': 'ANTICIPO/CLIENTE',
                    'account_id': payment.destination_account_id.id,  # anticipo
                    'partner_id': self.partner_id.id,
                    'debit': amount,
                    'credit': 0,
                    'foreign_currency_rate': payment.foreign_currency_rate,
                    'payment_id_advance': payment.id,
                    'reconciled': False,
                })]
            else:
                line_ret = [(0, 0, {
                    # tomar esta linea para reconciliar
                    'name': 'CUENTA POR PAGAR PROVEEDOR',
                    'account_id': cta,  # cuenta de la factura, CXP
                    'partner_id': self.partner_id.id,
                    'debit': amount,
                    'credit': 0,
                    'foreign_currency_rate': payment.foreign_currency_rate,
                    'payment_id_advance': payment.id,
                    'reconciled': False,
                }), (0, 0, {
                    'name': 'ANTICIPO/PROVEEDOR',
                    'account_id': payment.destination_account_id.id,  # Cuenta de anticipo configurada
                    'partner_id': self.partner_id.id,
                    'debit': 0,
                    'credit': amount,
                    'foreign_currency_rate': payment.foreign_currency_rate,
                    'payment_id_advance': payment.id,
                    'reconciled': False,
                })]
            move_obj = self.env['account.move'].create({
                'name': self.name + payment.name,
                'date': fields.Date.today(),
                'journal_id': payment.journal_id.id if payment.journal_id else 1,
                'state': 'draft',
                'line_ids': line_ret,
                'company_id': self.company_id.id,
                'foreign_currency_rate': payment.foreign_currency_rate,
                'foreign_currency_id': int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id')),
            })
            _logger.info('MOVIMIENTO PUENTE')
            _logger.info(move_obj)
            _logger.info('MOVIMIENTO PUENTE')
            move_obj.action_post()
            _logger.info('MOVIMIENTO PUBLICADO')
            _logger.info(move_obj.state)
            _logger.info('MOVIMIENTO PUBLICADO')
            cta_a = False
            for cfr in move_obj.line_ids:
                if cfr.name in ('ANTICIPO/CLIENTE', 'ANTICIPO/PROVEEDOR'):
                    cta_a = cfr.id
            linesa = self.env['account.move.line'].browse(cta_a)
            lines += linesa
            _logger.info('LINES')
            _logger.info(lines)
            _logger.info('LINES')
            lines.reconcile()
            _logger.info('RECONCILIADO LINES')
            cta_fv = False
            for cf in move_obj.line_ids:
                if cf.name in ('CUENTA POR COBRAR CLIENTE', 'CUENTA POR PAGAR PROVEEDOR'):
                    cta_fv = cf.id
                    break
            _logger.info('CTA_FV')
            _logger.info(cta_fv)
            _logger.info('CTA_FV')
            lines2 = self.env['account.move.line'].browse(cta_fv)
            _logger.info('lines2')
            _logger.info(lines2)
            _logger.info('lines2')
            lines2 += self.line_ids.filtered(lambda line: line.account_id == lines2[0].account_id and not line.reconciled)
            _logger.info('LINES2')
            _logger.info(lines2)
            _logger.info('LINES2')
            lines2.reconcile()
            return
        else:
            lines += self.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
            return lines.reconcile()

    def js_remove_outstanding_partial(self, partial_id):
        ''' Called by the 'payment' widget to remove a reconciled entry to the present invoice.

        :param partial_id: The id of an existing partial reconciled with the current invoice.
        '''
        self.ensure_one()
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        move_line_partial = self.env['account.move.line'].browse(partial.credit_move_id.id)
        if move_line_partial.payment_id_advance and move_line_partial.payment_id_advance.is_advance:
            move_line_partial.move_id.cancel_move()
            return
        move_line_partial = self.env['account.move.line'].browse(partial.debit_move_id.id)
        if move_line_partial.payment_id_advance and move_line_partial.payment_id_advance.is_advance:
            move_line_partial.move_id.cancel_move()
            return
        return partial.unlink()


class AccountMoveLineBinAdvance(models.Model):
    _inherit = "account.move.line"

    payment_id_advance = fields.Many2one('account.payment', string='Pago de anticipo asociado')

    def _compute_amount_residual(self):
        """ Computes the residual amount of a move line from a reconcilable account in the company currency and the line's currency.
            This amount will be 0 for fully reconciled lines or lines from a non-reconcilable account, the original line amount
            for unreconciled lines, and something in-between for partially reconciled lines.
        """
        for line in self:
            if line.id and (line.account_id.reconcile or line.account_id.internal_type == 'liquidity'):
                _logger.info('COMPUTE AMOUNT RESIDUAL')
                reconciled_balance = sum(line.matched_credit_ids.mapped('amount')) \
                                     - sum(line.matched_debit_ids.mapped('amount'))
                _logger.info('RECONCILED BALANCE')
                _logger.info(reconciled_balance)
                reconciled_amount_currency = sum(line.matched_credit_ids.mapped('debit_amount_currency')) \
                                             - sum(line.matched_debit_ids.mapped('credit_amount_currency'))
                _logger.info('RECONCILED AMOUNT CURRENCY')
                _logger.info(reconciled_amount_currency)
                line.amount_residual = line.balance - reconciled_balance
                _logger.info('LINE AMOUNT RESIDUAL')
                _logger.info(line.amount_residual)
                if line.currency_id:
                    line.amount_residual_currency = line.amount_currency - reconciled_amount_currency
                else:
                    line.amount_residual_currency = 0.0
                _logger.info('LINE AMOUNT RESIDUAL CURRENCY')
                _logger.info(line.amount_residual_currency)
                line.reconciled = line.company_currency_id.is_zero(line.amount_residual) \
                                  and (not line.currency_id or line.currency_id.is_zero(line.amount_residual_currency))
                _logger.info('LINE RECONCILED')
                _logger.info(line.reconciled)
            else:
                _logger.info('ELSE COMPUTE AMOUNT RESIDUAL')
                # Must not have any reconciliation since the line is not eligible for that.
                line.amount_residual = 0.0
                line.amount_residual_currency = 0.0
                line.reconciled = False

    def remove_move_reconcile(self):
        """ Undo a reconciliation """
        for deb in self.matched_debit_ids:
            _logger.info('AML MOVE DEBIT')
            _logger.info(deb.debit_move_id.move_id.id)
            _logger.info(deb.credit_move_id.move_id.id)
            if deb.debit_move_id.payment_id_advance:
                _logger.info('1')
                _logger.info(deb.debit_move_id.move_id.move_type)
                #if deb.debit_move_id.move_id.state == 'posted' and deb.debit_move_id.move_id.move_type == 'entry':
                #    deb.debit_move_id.move_id.cancel_move()
            if deb.credit_move_id.payment_id_advance:
                _logger.info('2')
                _logger.info(deb.credit_move_id.move_id.move_type)
                #if deb.credit_move_id.move_id.state == 'posted' and deb.credit_move_id.move_id.move_type == 'entry':
                #    deb.credit_move_id.move_id.cancel_move()
        for cred in self.matched_credit_ids:
            _logger.info('AML MOVE CREDIT')
            _logger.info(cred.debit_move_id.move_id.id)
            _logger.info(cred.credit_move_id.move_id.id)
            if cred.debit_move_id.payment_id_advance:
                _logger.info('3')
                _logger.info(cred.debit_move_id.move_id.move_type)
                #if cred.debit_move_id.move_id.state == 'posted' and cred.debit_move_id.move_id.move_type == 'entry':
                #    cred.debit_move_id.move_id.cancel_move()
            if cred.credit_move_id.payment_id_advance:
                _logger.info('4')
                _logger.info(cred.credit_move_id.move_id.move_type)
                if cred.credit_move_id.move_id.state == 'posted' and cred.credit_move_id.move_id.move_type == 'entry':
                    cred.credit_move_id.move_id.cancel_move()
        (self.matched_debit_ids + self.matched_credit_ids).unlink()

    def _reverse_moves(self, default_values_list=None, cancel=False):
        ''' Reverse a recordset of account.move.
        If cancel parameter is true, the reconcilable or liquidity lines
        of each original move will be reconciled with its reverse's.

        :param default_values_list: A list of default values to consider per move.
                                    ('type' & 'reversed_entry_id' are computed in the method).
        :return:                    An account.move recordset, reverse of the current self.
        '''
        if not default_values_list:
            default_values_list = [{} for move in self]
    
        if cancel:
            lines = self.mapped('line_ids')
            # Avoid maximum recursion depth.
            if lines:
                lines.remove_move_reconcile()
    
        reverse_type_map = {
            'entry': 'entry',
            'out_invoice': 'out_refund',
            'out_refund': 'entry',
            'in_invoice': 'in_refund',
            'in_refund': 'entry',
            'out_receipt': 'entry',
            'in_receipt': 'entry',
        }
    
        move_vals_list = []
        for move, default_values in zip(self, default_values_list):
            default_values.update({
                'move_type': reverse_type_map[move.move_type],
                'reversed_entry_id': move.id,
            })
            move_vals_list.append(
                move.with_context(move_reverse_cancel=cancel)._reverse_move_vals(default_values, cancel=cancel))
    
        reverse_moves = self.env['account.move'].create(move_vals_list)
        for move, reverse_move in zip(self, reverse_moves.with_context(check_move_validity=False)):
            # Update amount_currency if the date has changed.
            if move.date != reverse_move.date:
                for line in reverse_move.line_ids:
                    if line.currency_id:
                        line._onchange_currency()
            reverse_move._recompute_dynamic_lines(recompute_all_taxes=False)
        reverse_moves._check_balanced()
    
        # Reconcile moves together to cancel the previous one.
        if cancel:
            reverse_moves.with_context(move_reverse_cancel=cancel)._post(soft=False)
            for move, reverse_move in zip(self, reverse_moves):
                accounts = move.mapped('line_ids.account_id') \
                    .filtered(lambda account: account.reconcile or account.internal_type == 'liquidity')
                for account in accounts:
                    (move.line_ids + reverse_move.line_ids) \
                        .filtered(lambda line: line.account_id == account and not line.reconciled) \
                        .with_context(move_reverse_cancel=cancel) \
                        .reconcile()
    
        return reverse_moves
