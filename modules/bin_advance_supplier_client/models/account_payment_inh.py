# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError


class AccountPaymentInh(models.Model):
    _inherit = 'account.payment'

    is_advance = fields.Boolean(default=False, string="Anticipo", help="Este pago es un anticipo")

    @api.depends('journal_id', 'partner_id', 'partner_type', 'is_internal_transfer', 'is_advance')
    def _compute_destination_account_id(self):
        self.destination_account_id = False
        for pay in self:
            if pay.is_internal_transfer:
                pay.destination_account_id = pay.journal_id.company_id.transfer_account_id
            elif pay.partner_type == 'customer':
                # Receive money from invoice or send money to refund it.
                if pay.partner_id:
                    if pay.is_advance:
                        default_account = self.env['account.payment.config.advance'].search(
                            [('company_id', '=', self.env.user.company_id.id), ('active', '=', True),
                             ('advance_type', '=', 'customer')], limit=1)
                        if not default_account:
                            raise exceptions.UserError("Debe configurar la cuenta contable de anticipo %s-%s" % (pay.company_id.id, pay.partner_type))
                        pay.destination_account_id = default_account.advance_account_id.id
                    else:
                        pay.destination_account_id = pay.partner_id.with_company(pay.company_id).property_account_receivable_id
                else:
                    pay.destination_account_id = self.env['account.account'].search([
                        ('company_id', '=', pay.company_id.id),
                        ('internal_type', '=', 'receivable'),
                    ], limit=1)
            elif pay.partner_type == 'supplier':
                # Send money to pay a bill or receive money to refund it.
                if pay.partner_id:
                    if pay.is_advance:
                        default_account = self.env['account.payment.config.advance'].search(
                            [('company_id', '=', self.env.user.company_id.id), ('active', '=', True),
                             ('advance_type', '=', pay.partner_type)], limit=1)
                        if not default_account:
                            raise exceptions.UserError("Debe configurar la cuenta contable de anticipo")
                        pay.destination_account_id = default_account.advance_account_id.id
                    else:
                        pay.destination_account_id = pay.partner_id.with_company(pay.company_id).property_account_payable_id
                else:
                    pay.destination_account_id = self.env['account.account'].search([
                        ('company_id', '=', pay.company_id.id),
                        ('internal_type', '=', 'payable'),
                    ], limit=1)