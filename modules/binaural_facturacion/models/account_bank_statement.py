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
class AccountBankStatementLineBinauralFacturacion(models.Model):
    _inherit = 'account.bank.statement.line'
    """@api.model_create_multi
    def create(self, vals_list):


        st_lines = super().create(vals_list)
        _logger.info("vals_list en bank statement %s",vals_list)
        _logger.info("St lines in bank statement %s",st_lines)
        for i, st_line in enumerate(st_lines):
            rate = vals_list[i].get('foreign_currency_rate')
            st_line.move_id.write({'foreign_currency_rate':rate})

        return st_lines"""

    @api.onchange('amount','move_id.foreign_currency_rate','foreign_currency_rate')
    def onchange_rate_amount(self):
        _logger.info("DISPARO")
        for l in self:
            if l.statement_id.journal_id.currency_id != l.statement_id.journal_id.company_id.currency_id:
                #moneda de diario es distinta a moneda de company
                l.foreign_currency_id = l.statement_id.journal_id.company_id.currency_id
                l.amount_currency = l.amount/l.foreign_currency_rate if l.foreign_currency_rate > 0 else 0

