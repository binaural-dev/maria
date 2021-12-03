# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountBalanceReport(models.TransientModel):
    _inherit = "account.common.account.report"
    _name = 'account.balance.report'
    _description = 'Trial Balance Report'

    journal_ids = fields.Many2many('account.journal', 'account_report_trial_balance_journal_rel', 'account_id', 'journal_id', string='Journals', required=True)

    another_currency = fields.Boolean(string='En Bolivares')

    #sobreescribir
    target_move = fields.Selection([('posted', 'Todos los asientos validados'),
                                    ('all', 'Todos los asientos'),
                                    ], string='Movimientos destino', required=True, default='posted')

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update(self.read(['another_currency'])[0])
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref('accounting_pdf_reports.action_report_trial_balance').report_action(records, data=data)
