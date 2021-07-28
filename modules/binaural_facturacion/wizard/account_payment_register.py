import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountPaymentRegisterBinauralFacturacion(models.TransientModel):
    _inherit = 'account.payment.register'

    def default_alternate_currency(self):
        alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))

        if alternate_currency:
            return alternate_currency
        else:
            return False

    foreign_currency_id = fields.Many2one('res.currency', default=default_alternate_currency, tracking=True)
    foreign_currency_rate = fields.Monetary(string="Tasa", tracking=True, currency_field='foreign_currency_id')
    foreign_currency_date = fields.Date(string="Fecha", default=fields.Date.today(), tracking=True)

    @api.onchange('foreign_currency_id', 'foreign_currency_date')
    def _compute_foreign_currency_rate(self):
        for record in self:
            rate = self._get_rate(record.foreign_currency_id.id, record.foreign_currency_date, '<=')

            if rate:
                record.update({
                    'foreign_currency_rate': rate.rate,
                })
            else:
                rate = self._get_rate(record.foreign_currency_id.id, record.foreign_currency_date, '>=')
                if rate:
                    record.update({
                        'foreign_currency_rate': rate.rate,
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
