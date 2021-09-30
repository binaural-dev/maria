# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class HrExpenseBinaural(models.Model):
    _inherit = 'hr.expense'
    
    def default_alternate_currency(self):
        alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))

        if alternate_currency:
            return alternate_currency
        else:
            return False

    @api.onchange('foreign_currency_id', 'foreign_currency_date')
    def _compute_foreign_currency_rate(self):
        for record in self:
            rate = self.env['res.currency.rate'].search([('currency_id', '=', record.foreign_currency_id.id),
                                                         ('name', '<=', record.foreign_currency_date)], limit=1,
                                                        order='name desc')
            if rate:
                record.update({
                    'foreign_currency_rate': rate.rate,
                })
            else:
                rate = self.env['res.currency.rate'].search([('currency_id', '=', record.foreign_currency_id.id),
                                                             ('name', '>=', record.foreign_currency_date)], limit=1,
                                                            order='name asc')
                if rate:
                    record.update({
                        'foreign_currency_rate': rate.rate,
                    })
                else:
                    record.update({
                        'foreign_currency_rate': 0.00,
                    })

    @api.depends('total_amount', 'amount_residual', 'foreign_currency_rate')
    def _amount_all_foreign(self):
        """
        """
        for order in self:
            order.update({
                'foreign_total_amount': order.total_amount * order.foreign_currency_rate,
                'foreign_amount_residual': order.amount_residual * order.foreign_currency_rate,
            })

    def _get_account_move_line_values(self):
        move_line_values_by_expense = {}
        for expense in self:
            move_line_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            account_src = expense._get_expense_account_source()
            account_dst = expense._get_expense_account_destination()
            account_date = expense.sheet_id.accounting_date or expense.date or fields.Date.context_today(expense)
        
            company_currency = expense.company_id.currency_id
        
            move_line_values = []
            taxes = expense.tax_ids.with_context(round=True).compute_all(expense.unit_amount, expense.currency_id,
                                                                         expense.quantity, expense.product_id)
            total_amount = 0.0
            total_amount_currency = 0.0
            partner_id = expense.employee_id.sudo().address_home_id.commercial_partner_id.id
            foreign_currency_rate = expense.foreign_currency_rate
            _logger.info('TASA DE GASTOS')
            _logger.info(foreign_currency_rate)
            _logger.info('TASA DE GASTOS')
            # source move line
            balance = expense.currency_id._convert(taxes['total_excluded'], company_currency, expense.company_id,
                                                   account_date)
            amount_currency = taxes['total_excluded']
            move_line_src = {
                'name': move_line_name,
                'quantity': expense.quantity or 1,
                'debit': balance if balance > 0 else 0,
                'credit': -balance if balance < 0 else 0,
                'amount_currency': amount_currency,
                'account_id': account_src.id,
                'product_id': expense.product_id.id,
                'product_uom_id': expense.product_uom_id.id,
                'analytic_account_id': expense.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                'expense_id': expense.id,
                'partner_id': partner_id,
                'tax_ids': [(6, 0, expense.tax_ids.ids)],
                'tax_tag_ids': [(6, 0, taxes['base_tags'])],
                'currency_id': expense.currency_id.id,
                'foreign_currency_rate': foreign_currency_rate,
            }
            move_line_values.append(move_line_src)
            total_amount -= balance
            total_amount_currency -= move_line_src['amount_currency']
        
            # taxes move lines
            for tax in taxes['taxes']:
                balance = expense.currency_id._convert(tax['amount'], company_currency, expense.company_id,
                                                       account_date)
                amount_currency = tax['amount']
            
                if tax['tax_repartition_line_id']:
                    rep_ln = self.env['account.tax.repartition.line'].browse(tax['tax_repartition_line_id'])
                    base_amount = self.env['account.move']._get_base_amount_to_display(tax['base'], rep_ln)
                else:
                    base_amount = None
            
                move_line_tax_values = {
                    'name': tax['name'],
                    'quantity': 1,
                    'debit': balance if balance > 0 else 0,
                    'credit': -balance if balance < 0 else 0,
                    'amount_currency': amount_currency,
                    'account_id': tax['account_id'] or move_line_src['account_id'],
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'tax_tag_ids': tax['tag_ids'],
                    'tax_base_amount': base_amount,
                    'expense_id': expense.id,
                    'partner_id': partner_id,
                    'currency_id': expense.currency_id.id,
                    'analytic_account_id': expense.analytic_account_id.id if tax['analytic'] else False,
                    'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)] if tax['analytic'] else False,
                    'foreign_currency_rate': foreign_currency_rate,
                }
                total_amount -= balance
                total_amount_currency -= move_line_tax_values['amount_currency']
                move_line_values.append(move_line_tax_values)
        
            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': total_amount > 0 and total_amount,
                'credit': total_amount < 0 and -total_amount,
                'account_id': account_dst,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency,
                'currency_id': expense.currency_id.id,
                'expense_id': expense.id,
                'partner_id': partner_id,
                'foreign_currency_rate': foreign_currency_rate,
            }
            move_line_values.append(move_line_dst)
        
            move_line_values_by_expense[expense.id] = move_line_values
        return move_line_values_by_expense

    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_group_by_sheet = self._get_account_move_by_sheet()
    
        move_line_values_by_expense = self._get_account_move_line_values()
    
        for expense in self:
            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id != company_currency
        
            # get the account move of the related sheet
            move = move_group_by_sheet[expense.sheet_id.id]
        
            # get move line values
            move_line_values = move_line_values_by_expense.get(expense.id)
            move_line_dst = move_line_values[-1]
            total_amount = move_line_dst['debit'] or -move_line_dst['credit']
            total_amount_currency = move_line_dst['amount_currency']
        
            # create one more move line, a counterline for the total on payable account
            if expense.payment_mode == 'company_account':
                if not expense.sheet_id.bank_journal_id.default_account_id:
                    raise UserError(_("No account found for the %s journal, please configure one.") % (
                        expense.sheet_id.bank_journal_id.name))
                journal = expense.sheet_id.bank_journal_id
                # create payment
                payment_methods = journal.outbound_payment_method_ids if total_amount < 0 else journal.inbound_payment_method_ids
                journal_currency = journal.currency_id or journal.company_id.currency_id
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': 'outbound' if total_amount < 0 else 'inbound',
                    'partner_id': expense.employee_id.sudo().address_home_id.commercial_partner_id.id,
                    'partner_type': 'supplier',
                    'journal_id': journal.id,
                    'date': expense.date,
                    'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
                    'amount': abs(total_amount_currency) if different_currency else abs(total_amount),
                    'ref': expense.name,
                    'foreign_currency_rate': expense.foreign_currency_rate,
                })
        
            # link move lines to move, and move to expense sheet
            move.write({'line_ids': [(0, 0, line) for line in move_line_values]})
            expense.sheet_id.write({'account_move_id': move.id})
        
            if expense.payment_mode == 'company_account':
                expense.sheet_id.paid_expense_sheets()
    
        # post the moves
        for move in move_group_by_sheet.values():
            move._post()
    
        return move_group_by_sheet

    def _prepare_move_values(self):
        """
        This function prepares move values related to an expense
        """
        self.ensure_one()
        journal = self.sheet_id.bank_journal_id if self.payment_mode == 'company_account' else self.sheet_id.journal_id
        account_date = self.sheet_id.accounting_date or self.date
        move_values = {
            'journal_id': journal.id,
            'company_id': self.sheet_id.company_id.id,
            'date': account_date,
            'ref': self.sheet_id.name,
            # force the name to the default value, to avoid an eventual 'default_name' in the context
            # to set it to '' which cause no number to be given to the account.move when posted.
            'name': '/',
            'foreign_currency_rate': self.foreign_currency_rate,
        }
        return move_values

    foreign_currency_id = fields.Many2one('res.currency', default=default_alternate_currency,
                                          tracking=True)
    foreign_currency_rate = fields.Float(string="Tasa", tracking=True)
    foreign_currency_date = fields.Date(string="Fecha", default=fields.Date.today(), tracking=True)

    foreign_total_amount = fields.Monetary(string='Total moneda alterna', store=True, readonly=True,
                                             compute='_amount_all_foreign',
                                             tracking=5)
    foreign_amount_residual = fields.Monetary(string='Monto Adeudado alterno', store=True, readonly=True, compute='_amount_all_foreign')
