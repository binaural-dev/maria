# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round, float_repr
from odoo.tools.misc import formatLang, format_date
from odoo.exceptions import UserError, ValidationError

import time
import math
import base64
import re

import logging
_logger = logging.getLogger(__name__)


class AccountBankStatementBinauralFacturacion(models.Model):
    _inherit = 'account.bank.statement'

    check_rate = fields.Boolean(string='importes ajustados', default=False)

    @api.onchange('journal_id')
    def onchange_journal_bin(self):
        _logger.info("DISPARO PADRE")
        # resetear valores en caso de que diario tenga misma moneda que company
        if self.journal_id.currency_id == self.journal_id.company_id.currency_id or not self.journal_id.currency_id:
            for st_line in self.line_ids:
                st_line.update({'foreign_currency_id': False,
                               'amount_currency': False, 'foreign_currency_rate': False})

    def check_rates(self):
        _logger.info("check rates")
        for i in self:
            for st_line in self.line_ids:
                st_line.onchange_rate_amount()
            i.write({'check_rate': True})

    def button_post(self):
        _logger.info("check")

        if self.journal_id and self.journal_id.currency_id and self.journal_id.currency_id != self.journal_id.company_id.currency_id and not self.check_rate:
            # si tiene diario y es diferente al de la company
            raise ValidationError(
                "Debes ajustar importe por tasas antes de publicar")
        else:
            return super(AccountBankStatementBinauralFacturacion, self).button_post()


class AccountBankStatementLineBinauralFacturacion(models.Model):
    _inherit = 'account.bank.statement.line'

    @api.onchange('amount', 'move_id.foreign_currency_rate', 'foreign_currency_rate', 'statement_id.journal_id', 'move_id.journal_id', 'journal_id')
    def onchange_rate_amount(self):
        _logger.info("DISPARO")
        decimal_function = self.env['decimal.precision'].search(
            [('name', '=', 'decimal_quantity')])
        for l in self:
            company_currency = l.statement_id.journal_id.company_id.currency_id
            currency_id = l.statement_id.journal_id.currency_id
            if currency_id != company_currency:
                value_rate = decimal_function.getCurrencyValue(
                    rate=l.foreign_currency_rate, base_currency=currency_id.name, foreign_currency=company_currency.name)
                # moneda de diario es distinta a moneda de company
                l.foreign_currency_id = company_currency
                l.amount_currency = l.amount * value_rate
            else:
                l.foreign_currency_id = False
                l.amount_currency = False
