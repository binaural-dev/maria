# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from werkzeug.urls import url_encode
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrderBinauralCompras(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.onchange('filter_partner')
    def get_domain_partner(self):
        for record in self:
            record.partner_id = False
            if record.filter_partner == 'customer':
                return {'domain': {
                    'partner_id': [('customer_rank', '>=', 1)],
                }}
            elif record.filter_partner == 'supplier':
                return {'domain': {
                    'partner_id': [('supplier_rank', '>=', 1)],
                }}
            elif record.filter_partner == 'contact':
                return {'domain': {
                    'partner_id': [('supplier_rank', '=', 0), ('customer_rank', '=', 0)],
                }}
            else:
                return []

    phone = fields.Char(string='Teléfono', related='partner_id.phone')
    vat = fields.Char(string='RIF', compute='_get_vat')
    address = fields.Char(string='Dirección', related='partner_id.street')
    business_name = fields.Char(string='Razón Social', related='partner_id.business_name')
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, states=READONLY_STATES,\
                                 change_default=True, tracking=True,\
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    filter_partner = fields.Selection([('customer', 'Clientes'), ('supplier', 'Proveedores'), ('contact', 'Contactos')],
                                      string='Filtro de Contacto', default='supplier')

    amount_by_group = fields.Binary(string="Tax amount by group",compute='_compute_invoice_taxes_by_group',help='Edit Tax amounts if you encounter rounding issues.')

    amount_by_group_base = fields.Binary(string="Tax amount by group",compute='_compute_invoice_taxes_by_group',help='Edit Tax amounts if you encounter rounding issues.')

    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
        readonly=True, store=True,
        help='Utility field to express amount currency')
    @api.depends('partner_id')
    def _get_vat(self):
        for p in self:
            if p.partner_id.prefix_vat and p.partner_id.vat:
                vat = str(p.partner_id.prefix_vat) + str(p.partner_id.vat)
            else:
                vat = str(p.partner_id.vat)
            p.vat = vat.upper()


    @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.taxes_id', 'partner_id', 'currency_id')
    def _compute_invoice_taxes_by_group(self):
        ''' Helper to get the taxes grouped according their account.tax.group.
        This method is only used when printing the invoice.
        '''
        _logger.info("se ejecuto la funcion:_compute_invoice_taxes_by_group")
        for move in self:
            lang_env = move.with_context(lang=move.partner_id.lang).env
            tax_lines = move.order_line.filtered(lambda line: line.taxes_id)
            tax_balance_multiplicator = 1 #-1 if move.is_inbound(True) else 1
            res = {}
            # There are as many tax line as there are repartition lines
            done_taxes = set()
            for line in tax_lines:
                res.setdefault(line.taxes_id.tax_group_id, {'base': 0.0, 'amount': 0.0})
                _logger.info("line.price_subtotal en primer for %s",line.price_subtotal)
                res[line.taxes_id.tax_group_id]['base'] += tax_balance_multiplicator * (line.price_subtotal if line.currency_id else line.price_subtotal)
                #tax_key_add_base = tuple(move._get_tax_key_for_group_add_base(line))
                _logger.info("done_taxesdone_taxes %s",done_taxes)

                if line.currency_id and line.company_currency_id and line.currency_id != line.company_currency_id:
                    amount = line.company_currency_id._convert(line.price_tax, line.currency_id, line.company_id, line.date or fields.Date.context_today(self))
                else:
                    amount = line.price_tax
                res[line.taxes_id.tax_group_id]['amount'] += amount
                """if tax_key_add_base not in done_taxes:
                    _logger.info("line.price_tax en primer for %s",line.price_tax)
                    if line.currency_id and line.company_currency_id and line.currency_id != line.company_currency_id:
                        amount = line.company_currency_id._convert(line.price_tax, line.currency_id, line.company_id, line.date or fields.Date.context_today(self))
                    else:
                        amount = line.price_tax
                    res[line.taxes_id.tax_group_id]['amount'] += amount
                    # The base should be added ONCE
                    done_taxes.add(tax_key_add_base)"""

            # At this point we only want to keep the taxes with a zero amount since they do not
            # generate a tax line.
            zero_taxes = set()
            for line in move.order_line:
                for tax in line.taxes_id.flatten_taxes_hierarchy():
                    if tax.tax_group_id not in res or tax.tax_group_id in zero_taxes:
                        res.setdefault(tax.tax_group_id, {'base': 0.0, 'amount': 0.0})
                        res[tax.tax_group_id]['base'] += tax_balance_multiplicator * (line.price_subtotal if line.currency_id else line.price_subtotal)
                        zero_taxes.add(tax.tax_group_id)

            _logger.info("res========== %s",res)

            res = sorted(res.items(), key=lambda l: l[0].sequence)
            move.amount_by_group = [(
                group.name, amounts['amount'],
                amounts['base'],
                formatLang(lang_env, amounts['amount'], currency_obj=move.currency_id),
                formatLang(lang_env, amounts['base'], currency_obj=move.currency_id),
                len(res),
                group.id
            ) for group, amounts in res]

            move.amount_by_group_base = [(
                group.name.replace("IVA", "Base"), amounts['base'],
                amounts['amount'],
                formatLang(lang_env, amounts['base'], currency_obj=move.currency_id),
                formatLang(lang_env, amounts['amount'], currency_obj=move.currency_id),
                len(res),
                group.id
            ) for group, amounts in res]

    @api.model
    def _get_tax_key_for_group_add_base(self, line):
        """
        Useful for _compute_invoice_taxes_by_group
        must be consistent with _get_tax_grouping_key_from_tax_line
         @return list
        """
        return [line.taxes_id.id]


class PurchaseOrderLineBinauralCompras(models.Model):
    _inherit = 'purchase.order.line'
    
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
        readonly=True, store=True,
        help='Utility field to express amount currency')