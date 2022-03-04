# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime


class ArcvWizard(models.TransientModel):
    _name = 'arcv.wizard'
    _description = 'Genera el comprobante ARCV'

    partner_id = fields.Many2one('res.partner', string='Proveedor', required=True)
    date_init = fields.Date('Fecha de inicio', required=True)
    date_end = fields.Date('Fecha de culminación', required=True)
    correlative = fields.Char('Correlarivo')

    def sequence(self):
        sequence = self.env['ir.sequence'].search([('code', '=', 'sequence.arcv')])
        if not sequence:
            sequence = self.env['ir.sequence'].create({
                'name': 'Numero de control de ARCV',
                'code': 'arcv.control.number',
                'padding': 4
            })
        return sequence

    def print_arcv(self):
        foreign_currency_id = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
        decimal_function = self.env['decimal.precision'].search(
            [('name', '=', 'decimal_quantity')], limit=1)
        data_retention = []
        period_fiscal_month_init = datetime.datetime.strptime(str(self.date_init), "%Y-%m-%d").month
        period_fiscal_year_init = datetime.datetime.strptime(str(self.date_init), "%Y-%m-%d").year
        period_fiscal = datetime.datetime.strptime(str(self.date_init), "%Y-%m-%d")
        total_amount_year, total_amount_obj_retention_year, total_amount_ret_year = 0, 0, 0
        sequence = self.sequence()
        today = datetime.datetime.now()
        self.correlative = str(today.year) + sequence.next_by_code('sequence.arcv')

        all_tariffs = self.env['tarif.retention'].search([])
        retentions = self.env['account.retention'].search([('type_retention', '=', 'islr'), ('type', '=', 'in_invoice'),
                                                           ('partner_id', '=', self.partner_id.id),
                                                           ('state', '=', 'emitted')])
        while period_fiscal_month_init <= 12:
            for tariffs in all_tariffs:
                amount_obj_retention, amount_ret, amount_total = 0, 0, 0
                for retention in retentions:
                    if retention.date_accounting.month == period_fiscal_month_init and retention.date_accounting.year == period_fiscal_year_init:
                        for line in retention.retention_line:
                            if tariffs.percentage == line.related_percentage_tariffs:
                                if foreign_currency_id == 3:
                                    amount_obj_retention += line.foreign_facture_amount
                                    amount_ret += line.foreign_retention_amount
                                else:
                                    amount_obj_retention += line.facture_amount
                                    amount_ret += line.retention_amount
                                payment_register = self.env['account.payment'].search([])
                                for payment in payment_register:
                                    for payment_invoice in payment.reconciled_bill_ids:
                                        for line_invoice in line.invoice_id:
                                            if payment_invoice.id == line_invoice.id:
                                                if payment.currency_id.id == self.env.ref('base.VEF').id:
                                                    amount_total += payment.amount
                                                else:
                                                    value_rate = decimal_function.getCurrencyValue(
                                                        rate=payment.foreign_currency_rate, base_currency="USD", foreign_currency="VEF")
                                                    amount_total += (payment.amount * value_rate)
                if amount_ret > 0:
                    json_obj = {
                        'period': str(period_fiscal_month_init)+"/"+str(period_fiscal.year),
                        'tariff': tariffs.percentage,
                        'tariff_sub': tariffs.amount_sustract,
                        'amount_total': amount_total,
                        'amount_obj_retention': amount_obj_retention,
                        'amount_ret': amount_ret,
                    }
                    data_retention.append(json_obj)
                total_amount_year += amount_total
                total_amount_obj_retention_year += amount_obj_retention
                total_amount_ret_year += amount_ret
            period_fiscal_month_init += 1
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'period': {'init': self.date_init, 'end_day': datetime.datetime.strptime(str(self.date_end), "%Y-%m-%d").day, 'end_month': datetime.datetime.strptime(str(self.date_end), "%Y-%m-%d").month},
                'partner_id': {'id': self.partner_id.id, 'name': self.partner_id.name, 'street': self.partner_id.street, 'street2': self.partner_id.street2, 'phone': self.partner_id.phone,
                               'vat': (self.partner_id.prefix_vat + self.partner_id.vat) if self.partner_id.prefix_vat and self.partner_id.vat else self.partner_id.vat},
                'retentions': {'cant': len(data_retention), 'data': data_retention},
                'total_amount_year': total_amount_year,
                'total_amount_obj_retention_year': total_amount_obj_retention_year,
                'total_amount_ret_year': total_amount_ret_year,
                'correlative': self.correlative,
            },
        }
        return self.env.ref('binaural_reporte_fiscal.action_report_arcv').report_action(self, data=data)

