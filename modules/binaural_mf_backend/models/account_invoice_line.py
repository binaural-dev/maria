# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, pycompat, date_utils
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import re
import uuid
import json

class AccountMoveLineBinauralMFBackend(models.Model):
    _inherit = 'account.move.line'
    tax_ids = fields.Many2many('account.tax', string='Taxes', help="Taxes that apply on the base amount", check_company=True,domain=lambda self: [('id', 'in', self._get_domain_list())])

    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        if self.price_unit and self.move_id.is_sale_document(include_receipts=False):
            price_text = str(self.price_unit)
            splitter = price_text.split(".")
            if len(splitter) == 2:
                qty_entire = len(splitter[0])
                #la decimal siempre se asumira como 2 digitos
                if qty_entire > 9:
                    raise UserError("La cantidad de digitos en precio no puede ser mayor a 11 incluida la parte decimal")

    @api.model
    def _get_domain_list(self):
        taxes = self.env['account.tax'].search([('active', '=', True)])
        taxes_list = []
        already_exent = False
        for t in taxes:
            if t.caracter_tax_machine and t.amount > 0:
                taxes_list.append(t.id)
            elif not t.caracter_tax_machine and t.amount == 0 and not already_exent:
                already_exent = True
                taxes_list.append(t.id)
            else:
                pass
        return taxes_list


