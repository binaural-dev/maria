# -*- coding: utf-8 -*-

from email.policy import default
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class MunicipalityRetentions(models.Model):
    _name = 'account.municipality.retentions'
    _description = 'Retenciones Municipales'

    name = fields.Char(string="Numero de Comprobante", readonly=True)
    date = fields.Date(string="Fecha de Comprobante")
    type = fields.Selection(selection=[('out_invoice', 'Factura de Cliente'), (
        'in_invoice', 'Factura de Proveedor')], string="Tipo de Comprobante", readonly=True)
    date_accounting = fields.Date(string="Fecha Contable")
    partner_id = fields.Many2one('res.partner', string="Razon Social")
    retention_line_ids = fields.One2many(
        'account.municipality.retentions.line', 'retention_id', string="Retenciones")

    def get_sequence_municipality_retention(self):
        sequence = self.env['ir.sequence'].search(
            [('code', '=', 'retention.municipality.retention.control.number')])
        if not sequence:
            sequence = self.env['ir.sequence'].create({
                'name': 'Numero de control',
                'code': 'retention.municipality.retention.control.number',
                'padding': 5
            })
        return sequence.next_by_code('retention.municipality.retention.control.number')

    def action_validate(self):
        sequece = self.get_sequence_municipality_retention()
        for retention_line in self.retention_line_ids:

            retention_line.total_retained = retention_line.invoice_amount_untaxed * \
                (retention_line.activity_aliquot/100)
            self.get_rate_currency(
                retention_line.currency_id.name, retention_line.foreign_rate)
            retention_line.foreign_total_retained = self.get_rate_currency(
                retention_line.currency_id.name, retention_line.foreign_rate) * retention_line.total_retained
            invoice = self.env['account.move'].browse(
                retention_line.invoice_id.id)
            invoice.write({
                "municipality_tax_voucher": str(sequece),
                "municipality_tax": True
            })
        self.name = str(sequece)

    def get_rate_currency(self, currency_name, rate):
        decimal_function = self.env['decimal.precision'].search(
            [('name', '=', 'decimal_quantity')])
        foreign_currency_name = 'USD' if currency_name == 'VEF' else 'VEF'

        return decimal_function.getCurrencyValue(
            rate, currency_name, foreign_currency_name, 'CALC')


class MunicipalityRetentionsLine(models.Model):
    _name = "account.municipality.retentions.line"
    _description = 'Retenciones Municipales Linea'

    name = fields.Char(string="Descripcion", default="RET-Municipal")
    retention_id = fields.Many2one(
        'account.municipality.retentions', string="Retencion")
    invoice_id = fields.Many2one(
        'account.move', string='Factura', required=True)
    currency_id = fields.Many2one(
        'res.currency', string='Moneda', default=lambda self: self.env.user.company_id.currency_id)
    total_invoice = fields.Monetary(
        string="Total Facturado", related="invoice_id.amount_total")
    invoice_amount_untaxed = fields.Monetary(
        string="Base Imponible", related="invoice_id.amount_untaxed")
    economic_activity_id = fields.Many2one(
        'economic.activity', string="Actividad Economica")
    activity_aliquot = fields.Float(
        string="Aliquota", related="economic_activity_id.aliquot")
    total_retained = fields.Float(string="Retenido")
    foreign_rate = fields.Float(
        string="tasa foranea", related="invoice_id.foreign_currency_rate")
    foreign_total_invoice = fields.Monetary(
        string="Total Factura", related="invoice_id.foreign_amount_total")
    foreign_invoice_amount_untaxed = fields.Monetary(
        string="Total Factura", related="invoice_id.foreign_amount_untaxed")
    foreign_total_retained = fields.Float(string="Retenido Alterno")
    municipality_id = fields.Many2one(
        'res.country.municipality', string="Municipio", related="economic_activity_id.municipality_id")
