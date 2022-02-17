# -*- coding: utf-8 -*-

from odoo import api, fields, exceptions, http, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import xlsxwriter

from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from io import BytesIO
import logging
import time

from collections import OrderedDict
import pandas as pd

_logger = logging.getLogger(__name__)


class WizardAdvancePaymentReport(models.TransientModel):
    _name = "wizard.advance.payment.list"

    type_report = fields.Selection([
        ('supplier', 'Proveedor'),
        ('customer', 'Cliente'),
    ], string='Pagos de')

    type_payment = fields.Selection([
        ('advance', 'Anticipo'),
        ('payment', 'Pagos'),
        ('is_expense','Gastos'),
        ('all', 'Todos'),
    ], string='Tipo de pagos',default='advance')


    type_residual = fields.Selection([
        ('all', 'Todos'),
        ('with', 'Con saldo disponible'),
        ('zero','Sin saldo disponible'),
    ], string='Filtrar por saldo',default='all')


    all_partner = fields.Boolean(string='Todas las razones sociales',default=True)

    partner = fields.Many2one('res.partner', string='Razon Social')

    at_today  = fields.Boolean(string='A la fecha actual',default=True)

    start_date  = fields.Date(string='Desde',default=date.today().replace(day=1))

    end_date  = fields.Date(string='Hasta',default=date.today().replace(day=1)+relativedelta(months=1, days=-1))


    @api.onchange('all_partner')
    def _onchange_all_partner(self):
        if not self.all_partner:
            domain = []
            print("es un partner especifico, retornar domain")
            if self.type_report == 'supplier':
                domain = [('supplier_rank','>',0),('active','=',True)]
            else:
                domain = [('customer_rank','>',0),('active','=',True)]
        else:
            domain = []
        return {
            'domain': {
                'partner': domain,
            }
        }


    def print_pdf_payments(self):
        print("PRINT")
        if not self.type_report:
            raise UserError("Tipo de razon social es obligatorio")
        if not self.type_payment:
            raise UserError("Tipo de pago es obligatorio")
        if not self.all_partner and not self.partner:
            raise UserError("Razon social es obligatoria")
        if not self.at_today:
            if not self.start_date or not self.end_date:
                raise UserError("Fecha de inicio y fin obligatorias")
        if self.at_today:
            self.end_date = fields.Date.today()

        data = {'form':{'type_residual':self.type_residual,'type_report': self.type_report,'type_payment': self.type_payment,'all_partner':self.all_partner,'partner':self.partner.id,'at_today':self.at_today,'start_date':self.start_date,'end_date':self.end_date}}
        return self.env.ref('binaural_anticipos.action_report_advance_payment_report').with_context(landscape=True).report_action(self, data=data)


    def get_payments_by_partner(self,partner):
        print("obtener los pagos de ",partner)
        print("self",self)
        search_domain = []
        if self.type_report and self.type_report == 'supplier':
            search_domain += [('payment_type','=','outbound')]
        else:
            search_domain += [('payment_type','=','inbound')]

        if self.type_payment and self.type_payment == 'advance':
            search_domain += [('is_advance','=',True)]
        elif self.type_payment and self.type_payment == 'payment':
            search_domain += [('is_advance','=',False),('is_expense','=',False)]
        elif self.type_payment and self.type_payment == 'is_expense':
            search_domain += [('is_expense','=',True)]

        if self.at_today:
            search_domain += [('date','<=',fields.Date.today())]
        else:
            search_domain += [('date','<=',self.end_date),('date','>=',self.start_date)]
        if partner:
            search_domain += [('partner_id','=',partner.id)]
        search_domain += [('state', '=', 'posted')]
        payments = self.env['account.payment'].sudo().search(search_domain)


        if self.type_residual != 'all':
            print("filtrar por solo los que no tengan saldo")
            new_payments = []
            for p in payments:
                acum = self.get_residual_by_payment(p)
                if(acum == 0 and self.type_residual == 'zero') or (acum != 0 and self.type_residual == 'with'):
                    new_payments.append(p)
            return new_payments
        return payments

    def get_residual_by_payment(self,p):
        acum = 0
        if p:
            domain = [('partner_id', '=', self.env['res.partner']._find_accounting_partner(p.partner_id).id),
                      ('reconciled', '=', False),
                      ('move_id.state', '=', 'posted'),
                      '|',
                        '&', ('amount_residual_currency', '!=', 0.0), ('currency_id','!=', None),
                        '&', ('amount_residual_currency', '=', 0.0), '&', ('currency_id','=', None), ('amount_residual', '!=', 0.0)]
            if self.type_report == 'customer':

                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                
            else:

                domain.extend([('credit', '=', 0), ('debit', '>', 0)])

            lines = self.env['account.move.line'].search(domain)
            print("LINES",lines)
            #currency_id = self.currency_id
            if len(lines) != 0:
                for line in lines:
                    if line.payment_id.id == p.id:
                        acum += abs(line.amount_residual)
        return acum