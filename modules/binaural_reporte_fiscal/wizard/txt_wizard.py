# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from collections import OrderedDict
import pandas as pd
import math
from datetime import date


class TxtWizard(models.TransientModel):
    _name = 'txt.wizard'
    _description = 'Declarar el IVA ante el SENIAT'

    date_start = fields.Date('Fecha de inicio', default=date.today().replace(day=1))
    date_end = fields.Date('Fecha de termino', default=date.today().replace(day=1) + relativedelta(months=1, days=-1))

    def generte_txt(self):
        if self.date_start and self.date_end:
            retention_count = len(
                self.env['account.retention'].search([('date', '>=', self.date_start),
                                                      ('date', '<=', self.date_end),
                                                      ('state', '=', 'emitted'),
                                                      ('type_retention', '=', 'iva'),
                                                      ('type', '=', 'in_invoice')]).ids)
            if retention_count == 0:
                raise UserError("Facturas a pagar obligatorias")
        else:
            raise UserError("Facturas a pagar obligatorias")

        url = '/web/binary/download_txt?&date_start=%s&date_end=%s' % (self.date_start, self.date_end)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self'
        }

    def _retention_iva(self, docs):
        dic = OrderedDict([
            ('RIF del agente de retención', ''),
            ('Período impositivo', ''),
            ('Fecha de factura', ''),
            ('Tipo de operación', ''),
            ('Tipo de documento', ''),
            ('RIF de proveedor', ''),
            ('Número de documento', ''),
            ('Número de control', ''),
            ('Monto total del documento', 0.00),
            ('Base imponible', 0.00),
            ('Monto del Iva Retenido', 0.00),
            ('Número del documento afectado', ''),
            ('Número de comprobante de retención', 0),
            ('Monto exento del IVA', 0.00),
            ('Alícuota', 0.00),
            ('Número de Expediente', ''),
        ])
        lista = []
        for i in docs:
            for li in i.retention_line:
                dict = OrderedDict()
                dict.update(dic)
                dict['RIF del agente de retención'] = i.company_id.partner_id.vat

                pi = str(li.invoice_id.invoice_date)
                fpi = datetime.strptime(pi, '%Y-%m-%d')
                retet_date = str(i.date)  # fecha retencion
                frd = datetime.strptime(retet_date, '%Y-%m-%d')
                dict['Período impositivo'] = frd.strftime('%Y%m')  # basado en fecha de retencion
                dict['Fecha de factura'] = fpi.strftime('%Y-%m-%d')  # fecha de factura
                dict['Tipo de operación'] = 'C'
                td = '01' if i.type == 'in_invoice' else '02' if i.type == 'in_refund' else '03'
                dict['Tipo de documento'] = td
                dict['RIF de proveedor'] = i.partner_id.prefix_vat + i.partner_id.vat
                dict['Número de documento'] = li.invoice_id.name
                dict['Número de control'] = li.invoice_id.correlative
                dict['Número del documento afectado'] = li.invoice_id.invoice_origin or '0'
                dict['Número de comprobante de retención'] = int(i.number) or 0
                dict['Alícuota'] = li.tax_line
                # exento
                exento = 0.00
                if li.invoice_id.foreign_amount_by_group[-1][1] == 0.0:
                     exento = li.invoice_id.foreign_amount_by_group[-1][2]
                if not i.type == 'in_refund':
                    dict['Monto total del documento'] = li.foreign_facture_amount + li.foreign_iva_amount + exento or 0.00
                    dict['Base imponible'] = li.foreign_facture_amount or 0.00
                    dict['Monto del Iva Retenido'] = li.foreign_retention_amount or 0.00
                    dict['Monto exento del IVA'] = exento
                else:
                    dict['Monto total del documento'] = -li.foreign_facture_amount + li.foreign_iva_amount + exento or 0.00
                    dict['Base imponible'] = -li.foreign_facture_amount or 0.00
                    dict['Monto del Iva Retenido'] = -li.amount_tax_ret or 0.00
                    dict['Monto exento del IVA'] = -exento or 0.00
                dict['Número de Expediente'] = '0'
                lista.append(dict)
        tabla = pd.DataFrame(lista)
        return tabla, lista
