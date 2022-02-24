import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountPaymentRegisterBinauralFacturacion(models.TransientModel):
    _inherit = 'account.payment.register'

    def default_alternate_currency(self):
        alternate_currency = int(
            self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))

        if alternate_currency:
            return alternate_currency
        else:
            return False

    foreign_currency_id = fields.Many2one(
        'res.currency', default=default_alternate_currency, tracking=True)
    foreign_currency_rate = fields.Monetary(
        string="Tasa", tracking=True, currency_field='foreign_currency_id')
    foreign_currency_date = fields.Date(
        string="Fecha", default=fields.Date.today(), tracking=True)

    @api.onchange('foreign_currency_id', 'foreign_currency_date', 'foreign_currency_rate')
    def _compute_foreign_currency_rate(self):
        for record in self:
            if record.foreign_currency_rate == 0:
                rate = self._get_rate(
                    record.foreign_currency_id.id, record.foreign_currency_date, '<=')

                if rate:
                    record.update({
                        'foreign_currency_rate': rate.rate if rate.currency_id.name == 'VEF' else rate.vef_rate,
                    })
                else:
                    rate = self._get_rate(
                        record.foreign_currency_id.id, record.foreign_currency_date, '>=')
                    if rate:
                        record.update({
                            'foreign_currency_rate': rate.rate if rate.currency_id.name == 'VEF' else rate.vef_rate,
                        })
                    else:
                        record.update({
                            'foreign_currency_rate': 0.00,
                        })

    def _get_rate(self, foreign_currency_id, foreign_currency_date, operator):
        rate = self.env['res.currency.rate'].search([('currency_id', '=', foreign_currency_id),
                                                     ('name', operator, foreign_currency_date)], limit=1,
                                                    order='name desc')

        return rate

    def _create_payment_vals_from_wizard(self):
        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_id': self.payment_method_id.id,
            'destination_account_id': self.line_ids[0].account_id.id,
            'foreign_currency_rate': self.foreign_currency_rate,
        }

        if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
            payment_vals['write_off_line_vals'] = {
                'name': self.writeoff_label,
                'amount': self.payment_difference,
                'account_id': self.writeoff_account_id.id,
            }
        return payment_vals

    @api.model
    def _get_line_batch_key(self, line):
        ''' Turn the line passed as parameter to a dictionary defining on which way the lines
        will be grouped together.
        :return: A python dictionary.
        '''
        irModuleObj = self.env['ir.module.module']
        moduleIds = irModuleObj.sudo().search(
            [
                ('state', '=', 'installed'),
                ('name', '=', 'binaural_anticipos')
            ]
        )
        if moduleIds:
            ctas_anticipos = []
            for x in self.env['account.payment.config.advance'].search([('advance_type', '=', 'customer')], order='id desc'):
                ctas_anticipos.append(x.advance_account_id.id)
            return {
                'partner_id': line.partner_id.id,
                'account_id': line.account_id.id,
                'foreign_currency_rate': line.foreign_currency_rate,
                'currency_id': (line.currency_id or line.company_currency_id).id,
                'partner_bank_id': line.move_id.partner_bank_id.id,
                'partner_type': 'customer' if line.account_internal_type == 'receivable' or
                (line.account_id.user_type_id.type == 'other' and line.account_id.id in ctas_anticipos) else 'supplier',
                'payment_type': 'inbound' if line.balance > 0.0 else 'outbound',

            }
        else:
            return {
                'partner_id': line.partner_id.id,
                'account_id': line.account_id.id,
                'foreign_currency_rate': line.foreign_currency_rate,
                'currency_id': (line.currency_id or line.company_currency_id).id,
                'partner_bank_id': line.move_id.partner_bank_id.id,
                'partner_type': 'customer' if line.account_internal_type == 'receivable' else 'supplier',
                'payment_type': 'inbound' if line.balance > 0.0 else 'outbound',

            }

    @api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id',
                 'payment_date', 'foreign_currency_rate')
    def _compute_amount(self):
        for wizard in self:
            if wizard.source_currency_id == wizard.currency_id:
                # Same currency.
                wizard.amount = wizard.source_amount_currency
            elif wizard.currency_id == wizard.company_id.currency_id:
                # Payment expressed on the company's currency.
                wizard.amount = wizard.source_amount
            else:
                decimal_function = self.env['decimal.precision'].search(
                    [('name', '=', 'decimal_quantity')])
                rateToCalc = decimal_function.getCurrencyValue(rate=wizard.foreign_currency_rate, base_currency=wizard.company_id.currency_id.name,
                                                               foreign_currency=wizard.currency_id.name) if wizard.company_id.currency_id != wizard.currency_id else 1

                amount_payment_currency = wizard.source_amount * rateToCalc

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
                decimal_function = self.env['decimal.precision'].search(
                    [('name', '=', 'decimal_quantity')])
                rateToCalc = decimal_function.getCurrencyValue(rate=wizard.foreign_currency_rate, base_currency=wizard.company_id.currency_id.name,
                                                               foreign_currency=wizard.currency_id.name) if wizard.company_id.currency_id != wizard.currency_id else 1
                amount_payment_currency = wizard.source_amount * rateToCalc

                wizard.payment_difference = amount_payment_currency - wizard.amount
