# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class AccountPaymentInh(models.Model):
    _inherit = 'account.payment'

    is_advance = fields.Boolean(default=False, string="Anticipo", help="Este pago es un anticipo")

    def action_draft(self):
        ''' posted -> draft '''
        if self.move_igtf and self.is_igtf:
            self.move_igtf.button_draft()
        aml_anticipos = self.env['account.move.line'].search(
            [('payment_id_advance', '=', self.id)])
        if not aml_anticipos:
            self.move_id.button_draft()
        else:
            for aml in aml_anticipos.filtered(lambda line: line.move_id.state != 'cancel'):
                aml.move_id.cancel_move()
                _logger.info('IDS')
                _logger.info(aml.id)
            self.move_id.button_draft()

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

    def _seek_for_lines(self):
        ''' Helper used to dispatch the journal items between:
        - The lines using the temporary liquidity account.
        - The lines using the counterpart account.
        - The lines being the write-off lines.
        :return: (liquidity_lines, counterpart_lines, writeoff_lines)
        '''
        self.ensure_one()
    
        liquidity_lines = self.env['account.move.line']
        counterpart_lines = self.env['account.move.line']
        writeoff_lines = self.env['account.move.line']
    
        for line in self.move_id.line_ids:
            if line.account_id in (
                    self.journal_id.default_account_id,
                    self.journal_id.payment_debit_account_id,
                    self.journal_id.payment_credit_account_id,
            ):
                liquidity_lines += line
            elif line.account_id.internal_type in (
            'receivable', 'payable', 'other') or line.partner_id == line.company_id.partner_id:
                counterpart_lines += line
            else:
                writeoff_lines += line
    
        return liquidity_lines, counterpart_lines, writeoff_lines

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return
    
        for pay in self.with_context(skip_account_move_synchronization=True):
        
            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue
        
            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}
        
            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))
        
            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
            
                if len(liquidity_lines) != 1 or len(counterpart_lines) != 1:
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal entry must always contains:\n"
                        "- one journal item involving the outstanding payment/receipts account.\n"
                        "- one journal item involving a receivable/payable account.\n"
                        "- optional journal items, all sharing the same account.\n\n"
                    ) % move.display_name)
            
                if writeoff_lines and len(writeoff_lines.account_id) != 1:
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, all the write-off journal items must share the same account."
                    ) % move.display_name)
            
                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal items must share the same currency."
                    ) % move.display_name)
            
                if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal items must share the same partner."
                    ) % move.display_name)
                ctas_anticipos = []
                for x in self.env['account.payment.config.advance'].search([('advance_type', '=', 'customer')],
                                                                           order='id desc'):
                    ctas_anticipos.append(x.advance_account_id.id)
                if counterpart_lines.account_id.user_type_id.type == 'receivable' or \
                        (counterpart_lines.account_id.user_type_id.type == 'other' and counterpart_lines.account_id.id in ctas_anticipos):
                    partner_type = 'customer'
                else:
                    partner_type = 'supplier'
            
                liquidity_amount = liquidity_lines.amount_currency
            
                move_vals_to_write.update({
                    'currency_id': liquidity_lines.currency_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                payment_vals_to_write.update({
                    'amount': abs(liquidity_amount),
                    'payment_type': 'inbound' if liquidity_amount > 0.0 else 'outbound',
                    'partner_type': partner_type,
                    'currency_id': liquidity_lines.currency_id.id,
                    'destination_account_id': counterpart_lines.account_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
        
            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))