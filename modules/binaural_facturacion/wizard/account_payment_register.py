import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountPaymentRegisterBinauralFacturacion(models.TransientModel):
    _inherit = 'account.payment.register'


    foreign_currency_id = fields.Many2one('res.currency')
    foreign_currency_rate = fields.Monetary(string="Tasa", currency_field='foreign_currency_id')
    foreign_currency_date = fields.Date(string="Fecha")

    # @api.onchange('foreign_currency_id', 'foreign_currency_date')
    # def _compute_foreign_currency_rate(self):
    #     for record in self:
    #         rate = self._get_rate(record.foreign_currency_id.id, record.foreign_currency_date, '<=')
    #
    #         if rate:
    #             record.update({
    #                 'foreign_currency_rate': rate.rate,
    #             })
    #         else:
    #             rate = self._get_rate(record.foreign_currency_id.id, record.foreign_currency_date, '>=')
    #             if rate:
    #                 record.update({
    #                     'foreign_currency_rate': rate.rate,
    #                 })
    #             else:
    #                 record.update({
    #                     'foreign_currency_rate': 0.00,
    #                 })
    #
    # def _get_rate(self, foreign_currency_id, foreign_currency_date, operator):
    #     rate = self.env['res.currency.rate'].search([('currency_id', '=', foreign_currency_id),
    #                                                  ('name', operator, foreign_currency_date)], limit=1,
    #                                                 order='name desc')
    #     return rate

    @api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id',
                 'payment_date')
    def _compute_amount(self):
        for wizard in self:
            if wizard.source_currency_id == wizard.currency_id:
                # Same currency.
                wizard.amount = wizard.source_amount_currency
            elif wizard.currency_id == wizard.company_id.currency_id:
                # Payment expressed on the company's currency.
                wizard.amount = wizard.source_amount
            else:
                # Foreign currency on payment different than the one set on the journal entries.
                if wizard.currency_id.id == wizard.env.ref('base.VEF').id:
                    amount_payment_currency = wizard.source_amount * wizard.foreign_currency_rate
                else:
                    amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount,
                                                                                     wizard.currency_id,
                                                                                     wizard.company_id,
                                                                                     wizard.payment_date)
                wizard.amount = amount_payment_currency

    @api.depends('amount')
    def _compute_payment_difference(self):
        for wizard in self:
            if wizard.source_currency_id == wizard.currency_id:
                # Same currency.
                wizard.payment_difference = wizard.source_amount_currency - wizard.amount
            elif wizard.currency_id == wizard.company_id.currency_id:
                # Payment expressed on the company's currency.
                wizard.payment_difference = wizard.source_amount - wizard.amount
            else:
                if wizard.currency_id.id == wizard.env.ref('base.VEF').id:
                    amount_payment_currency = wizard.source_amount * wizard.foreign_currency_rate
                else:

                    # Foreign currency on payment different than the one set on the journal entries.
                    amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount,
                                                                                     wizard.currency_id, wizard.company_id,
                                                                                     wizard.payment_date)
                wizard.payment_difference = amount_payment_currency - wizard.amount