# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPickingBinauralInv(models.Model):
    _inherit = 'stock.picking'

    def _default_currency_id(self):
        return self.env.ref('base.VEF').id

    foreign_currency_id = fields.Many2one('res.currency', compute='_compute_foreign_currency')
    foreign_currency_rate = fields.Monetary(string="Tasa", tracking=True, currency_field='foreign_currency_id',
                                            compute='_compute_foreign_currency')

    @api.depends('origin')
    def _compute_foreign_currency(self):
        for record in self:
            foreign_currency_rate = foreign_currency_id = 0
            if record.origin:
                sale_id = record.env['sale.order'].search([('name', '=', record.origin)], limit=1)
                if sale_id:
                    foreign_currency_id = sale_id.currency_id.id
                    foreign_currency_rate = sale_id.foreign_currency_rate
            else:
                alternate_currency = int(record.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
                foreign_currency_id = alternate_currency
                rate = self.env['res.currency.rate'].search([('currency_id', '=', foreign_currency_id),
                                                             ('name', '<=', fields.Date.today())], limit=1,
                                                            order='name desc')
                foreign_currency_rate = rate.rate
            record.foreign_currency_id = foreign_currency_id
            record.foreign_currency_rate = foreign_currency_rate
