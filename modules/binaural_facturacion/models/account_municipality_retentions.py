# -*- coding: utf-8 -*-

from email.policy import default
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class MunicipalityRetentions(models.Model):
    _name = 'account.municipality.retentions'
    _description = 'Retenciones Municipales'

    name = fields.Char(string="Numero de Comprobante")
    date = fields.Date(string="Fecha de Comprobante")
    type = fields.Selection(selection=[('out_invoice', 'Factura de Cliente'), (
        'in_invoice', 'Factura de Proveedor')], string="Tipo de Comprobante", readonly=True)
    date_accounting = fields.Date(string="Fecha Contable")
    partner_id = fields.Many2one('res.partner', string="Razon Social")
    retention_line_ids = fields.One2many(
        'account.municipality.retentions.line', 'retention_id', string="Retenciones")


class MunicipalityRetentionsLine(models.Model):
    _name = "account.municipality.retentions.line"
    _description = 'Retenciones Municipales Linea'

    name = fields.Char(string="Descripcion")
    retention_id = fields.Many2one(
        'account.municipality.retentions', string="Retencion")
    invoice_id = fields.Many2one(
        'account.move', string='Factura', required=True)
    currency_id = fields.Many2one(
        'res.currency', string='Moneda', default=lambda self: self.env.user.company_id.currency_id)
    total_invoice = fields.Monetary(
        string="Total Factura", related="invoice_id.amount_total")
    invoice_amount_untaxed = fields.Monetary(
        string="Total Factura", related="invoice_id.amount_untaxed")
    economic_activity_id = fields.Many2one(
        'economic.activity', string="Actividad Economica")
    activity_aliquot = fields.Float(
        string="Aliquot", related="economic_activity_id.aliquot")
    total_retained = fields.Float(string="Retenido")
    foreign_total_invoice = fields.Monetary(
        string="Total Factura", related="invoice_id.foreign_amount_total")
    foreign_invoice_amount_untaxed = fields.Monetary(
        string="Total Factura", related="invoice_id.foreign_amount_untaxed")
    foreign_total_retained = fields.Float(string="Retenido Alterno")
