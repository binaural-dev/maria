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

    def _get_outstanding_info_JSON2(self):
        self.outstanding_credits_debits_widget2 = json.dumps(False)
        if self.payment_state in ['not_paid', 'in_payment', 'partial']:
            domain = [('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                      ('has_reconciled_entries', '=', False),
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
                self.has_outstanding = True


class AccountMoveLineBinAdvance(models.Model):
    _inherit = "account.move.line"

    payment_id_advance = fields.Many2one('account.payment', string='Pago de anticipo asociado')
