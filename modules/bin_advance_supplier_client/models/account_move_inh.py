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

    def _compute_payments_widget_to_reconcile_info2(self):
        for move in self:
            move.invoice_outstanding_credits_debits_widget = json.dumps(False)
            move.invoice_has_outstanding = False
        
            if move.state != 'posted' \
                    or move.payment_state not in ('not_paid', 'partial') \
                    or not move.is_invoice(include_receipts=True):
                continue
        
            pay_term_lines = move.line_ids \
                .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        
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
        _logger.info('LINE_ID')
        _logger.info(line_id)
        lines = self.env['account.move.line'].browse(line_id)
        _logger.info('LINES')
        _logger.info(lines)
        lines += self.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
        return lines.reconcile()


class AccountMoveLineBinAdvance(models.Model):
    _inherit = "account.move.line"

    payment_id_advance = fields.Many2one('account.payment', string='Pago de anticipo asociado')
