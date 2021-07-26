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
    foreign_currency_rate = fields.Float(string="Tasa", tracking=True, default=default_currency_rate,
                                         currency_field='foreign_currency_id')
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

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        flag = False
        rate = 0
        for record in vals_list:
            rate = record.get('foreign_currency_rate', False)
            if rate:
                rate = round(rate, 2)
                alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
                if alternate_currency:
                    currency = self.env['res.currency.rate'].search([('currency_id', '=', alternate_currency)], limit=1,
                                                                    order='name desc')
                    if rate != currency.rate:
                        flag = True
        res = super(AccountPaymentBinauralFacturacion, self).create(vals_list)
        if flag:
            # El usuario xxxx ha usado una tasa personalizada, la tasa del sistema para la fecha del pago xxx es de xxxx y ha usada la tasa personalizada xxx
            display_msg = "El usuario " + self.env.user.name + "ha usado una tasa personalizada,"
            display_msg += " la tasa del sistema para la fecha del pago " + str(fields.Date.today())
            display_msg += " y ha usada la tasa personalizada " + str(rate)
            res.message_post(body=display_msg)
        return res

    # def _prepare_move_line_default_vals(self, write_off_line_vals=None):
    #     """enviar tasa al crear el pago"""
    #     res = super(AccountPaymentBinauralFacturacion, self)._prepare_move_line_default_vals(write_off_line_vals)
    #     for record in res:
    #         record.setdefault('foreign_currency_rate', self.foreign_currency_rate)
    #     return res
