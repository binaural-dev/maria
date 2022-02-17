# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountCommonAccountReport(models.TransientModel):
    _name = 'account.common.account.report'
    _description = 'Account Common Account Report'
    _inherit = "account.common.report"

    display_account = fields.Selection([('all', 'Todo'), ('movement', 'Con movimientos'),
                                        ('not_zero', 'Con saldo distinto a 0'), ],
                                       string='Display Accounts', required=True, default='all')

    def pre_print_report(self, data):
        data['form'].update(self.read(['display_account'])[0])
        return data
