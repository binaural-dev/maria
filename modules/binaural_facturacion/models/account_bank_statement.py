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
    @api.onchange('journal_id')
    def onchange_journal_bin(self):
        _logger.info("DISPARO PADRE")
        #resetear valores en caso de que diario tenga misma moneda que company
        if self.journal_id.currency_id == self.journal_id.company_id.currency_id or not self.journal_id.currency_id:
            for st_line in self.line_ids:
                st_line.update({'foreign_currency_id':False,'amount_currency':False,'foreign_currency_rate':False})



class AccountBankStatementLineBinauralFacturacion(models.Model):
    _inherit = 'account.bank.statement.line'
    @api.onchange('amount','move_id.foreign_currency_rate','foreign_currency_rate','statement_id.journal_id','move_id.journal_id','journal_id')
    def onchange_rate_amount(self):
        _logger.info("DISPARO")
        for l in self:
            if l.statement_id.journal_id.currency_id != l.statement_id.journal_id.company_id.currency_id:
                #moneda de diario es distinta a moneda de company
                l.foreign_currency_id = l.statement_id.journal_id.company_id.currency_id
                l.amount_currency = l.amount/l.foreign_currency_rate if l.foreign_currency_rate > 0 else 0
            else:
                l.foreign_currency_id = False
                l.amount_currency = False
