# -*- coding: utf-8 -*-

from odoo import models, api, exceptions, fields


class AccountPaymentAction(models.Model):
    _inherit = 'account.payment'

    @api.onchange('partner_id')
    def _get_action_number(self):
        for record in self:
            record.action_number = record.partner_id.action_number.number

    action_number = fields.Char(string='Número de Acción')