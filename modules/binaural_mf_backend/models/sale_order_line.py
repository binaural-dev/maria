# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, pycompat, date_utils
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import re
import uuid
import json


class SaleOrderLineBinauralMFBackend(models.Model):
    _inherit = 'sale.order.line'

    tax_id = fields.Many2many('account.tax', string='Taxes', domain=lambda self: [('id', 'in', self._get_domain_list())])
    
    @api.model
    def _get_domain_list(self):
        taxes = self.env['account.tax'].search([('active','=',True)])
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


