# -*- coding: utf-8 -*-

from odoo import models, fields, api


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

    foreign_currency_id = fields.Many2one('res.currency', default=default_alternate_currency,
                                          tracking=True)
    foreign_currency_rate = fields.Float(string="Tasa", tracking=True)
    foreign_currency_date = fields.Date(string="Fecha", default=fields.Date.today(), tracking=True)

    foreign_total_amount = fields.Monetary(string='Total moneda alterna', store=True, readonly=True,
                                             compute='_amount_all_foreign',
                                             tracking=5)
    foreign_amount_residual = fields.Monetary(string='Monto Adeudado alterno', store=True, readonly=True, compute='_amount_all_foreign')
