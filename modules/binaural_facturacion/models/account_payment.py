from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
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


class AccountPaymentBinauralFacturacion(models.Model):
    _inherit = 'account.payment'

    def default_alternate_currency(self):
        alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))

        if alternate_currency:
            return alternate_currency
        else:
            return False

    def default_currency_rate(self):
        rate = 0
        alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
        if alternate_currency:
            currency = self.env['res.currency.rate'].search([('currency_id', '=', alternate_currency)], limit=1,
                                                            order='name desc')
            rate = currency.rate

        return rate

    foreign_currency_id = fields.Many2one('res.currency', default=default_alternate_currency, tracking=True)
    foreign_currency_rate = fields.Float(string="Tasa", tracking=True, default=default_currency_rate)
    foreign_currency_date = fields.Date(string="Fecha", default=fields.Date.today(), tracking=True)

    @api.onchange('foreign_currency_id', 'foreign_currency_date')
    def _compute_foreign_currency_rate(self):
        for record in self:
            rate = self._get_rate(record.foreign_currency_id.id, record.foreign_currency_date, '<=')

            if rate:
                record.update({
                    'foreign_currency_rate': rate.rate,
                })
            else:
                rate = self._get_rate(record.foreign_currency_id.id, record.foreign_currency_date, '>=')
                if rate:
                    record.update({
                        'foreign_currency_rate': rate.rate,
                    })
                else:
                    record.update({
                        'foreign_currency_rate': 0.00,
                    })

    def _get_rate(self, foreign_currency_id, foreign_currency_date, operator):
        rate = self.env['res.currency.rate'].search([('currency_id', '=', foreign_currency_id),
                                                     ('name', operator, foreign_currency_date)], limit=1,
                                                    order='name desc')
        return rate
