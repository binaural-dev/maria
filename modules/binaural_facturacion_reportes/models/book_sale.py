from openerp import models, fields, api, exceptions
from collections import OrderedDict
import pandas as pd
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class BookSaleReport(models.TransientModel):
    _inherit = 'wizard.accounting.reports'

    def _sale_book_invoice(self):
        search_domain = self._get_domain()
        search_domain += [
            ('state', 'not in', ['draft']),
            ('move_type', 'in', ['out_invoice', 'out_refund', 'out_debit']),
            ('journal_id.fiscal', '=', True)
        ]
        docs = self.env['account.move'].search(search_domain, order='id asc')
        docs_ids = self.env['account.move'].search(
            search_domain, order='name asc').ids
        dic = OrderedDict([
            ('Nª de Ope', 0),
            ('Fecha', ''),
            ('R.I.F', ''),
            ('Nombre/Razón Social', ''),
            ('Tipo', ''),
            ('Nª de Doc', ''),
            ('Nª de Control', ''),
            ('Tipo Transacción', ''),
            ('Nª de Doc. Afectado', ''),
            ('Total Ventas incluye IVA', 0.00),
            ('Total Ventas Exentas', 0.00),
            ('Imponible16', 0.00),
            ('%16', 0.00),
            ('Impuesto16', 0.00),
            ('Imponible8', 0.00),
            ('%8', 0.00),
            ('Impuesto8', 0.00),
            ('Retenciones', 0.00),
            ('Comprobante de Ret.', ''),
            ('Fecha de Comprobante', ''),
        ])
        lista = []
        invoices = []
        op = 1
        for i in docs:
            invoices.append(i.id)
            amount_retention = 0.00
            retention_number = ''
            retention_date = False
            search_domain_rt = [
                ('invoice_id', '=', i.id),('retention_id.date_accounting','>=',self.date_start),('retention_id.date_accounting','<=',self.date_end),
                ('retention_id.type_retention', '=', 'iva')
            ]
            retention_lines = self.env['account.retention.line'].search(search_domain_rt)
            for x in retention_lines:
                if x.retention_id.state in ['emitted']:
                    if self.currency_sistem:
                        amount_retention += x.retention_amount
                    else:
                        amount_retention += x.foreign_retention_amount
                    retention_number = x.retention_id.number
                    retention_date = x.retention_id.date_accounting
            dict = OrderedDict()
            dict.update(dic)
            base = 0.00
            base16 = 0.00
            base8 = 0.00
            imp16 = 0.00
            imp8 = 0.00
            not_gravable = 0.00
            if self.currency_sistem:
                for line in i.amount_by_group:
                    tax_id = self.env['account.tax'].search(
                        [('tax_group_id', '=', line[6]), ('type_tax_use', '=', 'sale')], limit=1)
                    if tax_id.amount > 0:
                        if tax_id.amount == 16:
                            base16 = line[2]
                            imp16 = line[1]
                        if tax_id.amount == 8:
                            base8 = line[2]
                            imp8 = line[1]
                        base += line[2]
                    else:
                        not_gravable += line[2]
            else:
                for line in i.foreign_amount_by_group:
                    tax_id = self.env['account.tax'].search(
                        [('tax_group_id', '=', line[6]), ('type_tax_use', '=', 'sale')], limit=1)
                    if tax_id.amount > 0:
                        if tax_id.amount == 16:
                            base16 = line[2]
                            imp16 = line[1]
                        if tax_id.amount == 8:
                            base8 = line[2]
                            imp8 = line[1]
                        base += line[2]
                    else:
                        not_gravable += line[2]
            dict['Nª de Ope'] = 0
            f = i.invoice_date
            fn = datetime.strptime(str(f), '%Y-%m-%d')
            dict['Fecha'] = fn.strftime('%d/%m/%Y')
            dict['R.I.F'] = i.partner_id.prefix_vat + i.partner_id.vat
            dict['Nombre/Razón Social'] = i.partner_id.name
            if i.move_type in ['out_invoice']:
                dict['Tipo'] = 'FAC'
            elif i.move_type == 'out_refund':
                dict['Tipo'] = 'NC'
            else:
                dict['Tipo'] = 'ND'
            dict['Nª de Doc'] = i.name
            dict['Nª de Control'] = i.correlative
            if i.move_type in ['out_invoice'] and i.state in ['posted']:
                dict['Tipo Transacción'] = '01-REG'
            if i.move_type in ['out_invoice'] and i.state in ['cancel']:
                dict['Tipo Transacción'] = '03-ANU'
            if i.move_type in ['out_refund','out_debit'] and i.state in ['posted']:
                dict['Tipo Transacción'] = '02-REG'
            if i.move_type in ['out_refund','out_debit'] and i.state in ['cancel']:
                dict['Tipo Transacción'] = '03-ANU'
            dict['Nª de Doc. Afectado'] = i.reversed_entry_id.name if i.reversed_entry_id else ''
            
            
            if i.state in ['posted']:
                if self.currency_sistem:
                    dict['Total Ventas incluye IVA'] = i.amount_total if i.move_type in ['out_invoice','out_debit'] else -i.amount_total
                    dict['Total Ventas Exentas'] = not_gravable if i.move_type in ['out_invoice','out_debit'] else -not_gravable
                    dict['Imponible16'] = base16 if i.move_type in ['out_invoice','out_debit'] else -base16
                    dict['%16'] = 0.16
                    dict['Impuesto16'] = imp16 if i.move_type in ['out_invoice','out_debit'] else -imp16
                    dict['Imponible8'] = base8 if i.move_type in ['out_invoice', 'out_debit'] else -base8
                    dict['%8'] = 0.08
                    dict['Impuesto8'] = imp8 if i.move_type in ['out_invoice', 'out_debit'] else -imp8
                    dict['Retenciones'] = amount_retention if i.move_type in ['out_invoice', 'out_debit'] else -amount_retention
                else:
                    dict['Total Ventas incluye IVA'] = i.foreign_amount_total if i.move_type in ['out_invoice',
                                                                                         'out_debit'] else -i.foreign_amount_total
                    dict['Total Ventas Exentas'] = not_gravable if i.move_type in ['out_invoice',
                                                                                   'out_debit'] else -not_gravable
                    dict['Imponible16'] = base16 if i.move_type in ['out_invoice', 'out_debit'] else -base16
                    dict['%16'] = 0.16
                    dict['Impuesto16'] = imp16 if i.move_type in ['out_invoice', 'out_debit'] else -imp16
                    dict['Imponible8'] = base8 if i.move_type in ['out_invoice', 'out_debit'] else -base8
                    dict['%8'] = 0.08
                    dict['Impuesto8'] = imp8 if i.move_type in ['out_invoice', 'out_debit'] else -imp8
                    dict['Retenciones'] = amount_retention if i.move_type in ['out_invoice',
                                                                              'out_debit'] else -amount_retention
                
                
                dict['Comprobante de Ret.'] = retention_number
                if retention_date:
                    fr = retention_date
                    fnr = datetime.strptime(str(fr), '%Y-%m-%d')
                    dict['Fecha de Comprobante'] = fnr.strftime('%d/%m/%Y')
                else:
                    dict['Fecha de Comprobante'] = ''
            else:
                dict['Total Ventas incluye IVA'] = 0.00
                dict['Total Ventas Exentas'] = 0.00
                dict['Imponible16'] = 0.00
                dict['%16'] = 0.16
                dict['Impuesto16'] = 0.00
                dict['Imponible8'] = 0.00
                dict['%8'] = 0.08
                dict['Impuesto8'] = 0.00
                dict['Retenciones'] = 0.00
                dict['Comprobante de Ret.'] = ''
                dict['Fecha de Comprobante'] = ''
            lista.append(dict)
        search_domain_only_retention = [
            ('retention_id.date_accounting', '>=', self.date_start),
            ('retention_id.date_accounting', '<=', self.date_end),
            ('retention_id.type', 'in', ['out_invoice', 'out_refund', 'out_debit', 'out_contingence']),
            ('retention_id.type_retention', '=', 'iva'),
            ('retention_id.state', 'in', ['emitted'])
        ]
        retention_lines_only = self.env['account.retention.line'].search(search_domain_only_retention)
        for x in retention_lines_only:
            if x.invoice_id.id not in invoices:
                dict = OrderedDict()
                dict.update(dic)
                dict['Nª de Ope'] = 0
                f = x.invoice_id.invoice_date
                fn = datetime.strptime(str(f), '%Y-%m-%d')
                dict['Fecha'] = fn.strftime('%d/%m/%Y')
                dict['R.I.F'] = x.invoice_id.partner_id.prefix_vat + x.invoice_id.partner_id.vat
                dict['Nombre/Razón Social'] = x.invoice_id.partner_id.name
                if x.invoice_id.move_type in ['out_invoice']:
                    dict['Tipo'] = 'FAC'
                elif x.invoice_id.move_type == 'out_refund':
                    dict['Tipo'] = 'NC'
                else:
                    dict['Tipo'] = 'ND'
                dict['Nª de Doc'] = x.invoice_id.name
                dict['Nª de Control'] = x.invoice_id.correlative
                if x.invoice_id.move_type in ['out_invoice'] and x.invoice_id.state in ['posted']:
                    dict['Tipo Transacción'] = '01-REG'
                if x.invoice_id.move_type in ['out_invoice'] and x.invoice_id.state in ['cancel']:
                    dict['Tipo Transacción'] = '03-ANU'
                if x.invoice_id.move_type in ['out_refund', 'out_debit'] and x.invoice_id.state in ['posted']:
                    dict['Tipo Transacción'] = '02-REG'
                if x.invoice_id.move_type in ['out_refund', 'out_debit'] and x.invoice_id.state in ['cancel']:
                    dict['Tipo Transacción'] = '03-ANU'
                dict['Nª de Doc. Afectado'] = x.invoice_id.reversed_entry_id.name if x.invoice_id.reversed_entry_id else ''
                dict['Total Ventas incluye IVA'] = 0.00
                dict['Total Ventas Exentas'] = 0.00
                dict['Imponible16'] = 0.00
                dict['%16'] = 0.16
                dict['Impuesto16'] = 0.00
                dict['Imponible8'] = 0.00
                dict['%8'] = 0.08
                dict['Impuesto8'] = 0.00
                if self.currency_sistem:
                    dict['Retenciones'] = x.retention_amount
                else:
                    dict['Retenciones'] = x.foreign_retention_amount
                dict['Comprobante de Ret.'] = x.retention_id.number
                if x.retention_id.date_accounting:
                    fr = x.retention_id.date_accounting
                    fnr = datetime.strptime(str(fr), '%Y-%m-%d')
                    dict['Fecha de Comprobante'] = fnr.strftime('%d/%m/%Y')
                else:
                    dict['Fecha de Comprobante'] = ''
                lista.append(dict)
        lista.sort(key=lambda date: datetime.strptime(date['Fecha'], "%d/%m/%Y"))
        for item in lista:
            item['Nª de Ope'] = op
            op += 1
        tabla = pd.DataFrame(lista)
        return tabla

    def sum_sale_book_invoice(self):
        tabla = self._sale_book_invoice()
        tabla.columns = tabla.columns.map(lambda x: x.replace(' ', '_'))
        sum_tabla = tabla.sum(axis=0, skipna=True)
        return sum_tabla

    def _sale_book_invoice_resumen_excel(self):
        dic = self.det_columns_resumen()
        tabla = self._sale_book_invoice()
        _logger.info(tabla)
        if len(tabla.columns) >0:
            tabla.columns = tabla.columns.map(lambda x: x.replace(' ', '_'))
            _logger.info('columnas')
            _logger.info('columnas')
            _logger.info('columnas')
            _logger.info('columnas')
            _logger.info('columnas')
            _logger.info(tabla.columns)
            is_fact = tabla['Tipo'] == 'FAC'
            is_nd = tabla['Tipo'] == 'ND'
            is_nc = tabla['Tipo'] == 'NC'
            _logger.info(is_nd)
            tabla_fan = tabla[is_fact]
            tabla_nd = tabla[is_nd]
            tabla_nc = tabla[is_nc]
            sum_tabla_fan = tabla_fan.sum(axis=0, skipna=True)
            sum_tabla_nd = tabla_nd.sum(axis=0, skipna=True)
            sum_tabla_nc = tabla_nc.sum(axis=0, skipna=True)
            _logger.info('nd')
            _logger.info('nd')
            _logger.info(sum_tabla_nd)
            lista = []
            dict = OrderedDict()
            dict.update(dic)
            dict['_1'] = 1
            dict['_2'] = 'Ventas Internas No Gravadas'
            dict['_3'] = sum_tabla_fan['Total_Ventas_Exentas'] + sum_tabla_nd['Total_Ventas_Exentas']
            dict['_4'] = 0.00
            dict['_5'] = sum_tabla_nc['Total_Ventas_Exentas']
            dict['_6'] = 0.00
            dict['_7'] = sum_tabla_fan['Total_Ventas_Exentas'] + sum_tabla_nd['Total_Ventas_Exentas'] + sum_tabla_nc['Total_Ventas_Exentas']
            dict['_8'] = 0.00
            lista.append(dict)
            dict = OrderedDict()
            dict.update(dic)
            dict['_1'] = 2
            dict['_2'] = 'Exportaciones Gravadas por Alícuota General'
            dict['_3'] = 0.00
            dict['_4'] = 0.00
            dict['_5'] = 0.00
            dict['_6'] = 0.00
            dict['_7'] = 0.00
            dict['_8'] = 0.00
            lista.append(dict)
            dict = OrderedDict()
            dict.update(dic)
            dict['_1'] = 3
            dict['_2'] = 'Exportaciones Gravadas por Alícuota General más Adicional'
            dict['_3'] = 0.00
            dict['_4'] = 0.00
            dict['_5'] = 0.00
            dict['_6'] = 0.00
            dict['_7'] = 0.00
            dict['_8'] = 0.00
            lista.append(dict)
            dict = OrderedDict()
            dict.update(dic)
            dict['_1'] = 4
            dict['_2'] = 'Ventas Internas Gravadas sólo por Alícuota General'
            dict['_3'] = sum_tabla_fan['Imponible16'] + sum_tabla_nd['Imponible16']
            dict['_4'] = sum_tabla_fan['Impuesto16'] + sum_tabla_nd['Impuesto16']
            dict['_5'] = sum_tabla_nc['Imponible16']
            dict['_6'] = sum_tabla_nc['Impuesto16']
            dict['_7'] = sum_tabla_fan['Imponible16'] + sum_tabla_nd['Imponible16'] + sum_tabla_nc['Imponible16']
            dict['_8'] = sum_tabla_fan['Impuesto16'] + sum_tabla_nd['Impuesto16'] + sum_tabla_nc['Impuesto16']
            lista.append(dict)
            dict = OrderedDict()
            dict.update(dic)
            dict['_1'] = 5
            dict['_2'] = 'Ventas Internas Gravadas por Alícuota General más Adicional'
            dict['_3'] = 0.00
            dict['_4'] = 0.00
            dict['_5'] = 0.00
            dict['_6'] = 0.00
            dict['_7'] = 0.00
            dict['_8'] = 0.00
            lista.append(dict)
            dict = OrderedDict()
            dict.update(dic)
            dict['_1'] = 6
            dict['_2'] = 'Ventas Internas Gravadas por Alícuota Reducida'
            dict['_3'] = sum_tabla_fan['Imponible8'] + sum_tabla_nd['Imponible8']
            dict['_4'] = sum_tabla_fan['Impuesto8'] + sum_tabla_nd['Impuesto8']
            dict['_5'] = sum_tabla_nc['Imponible8']
            dict['_6'] = sum_tabla_nc['Impuesto8']
            dict['_7'] = sum_tabla_fan['Imponible8'] + sum_tabla_nd['Imponible8'] + sum_tabla_nc['Imponible8']
            dict['_8'] = sum_tabla_fan['Impuesto8'] + sum_tabla_nd['Impuesto8'] + sum_tabla_nc['Impuesto8']
            lista.append(dict)
            dict = OrderedDict()
            dict.update(dic)
            dict['_1'] = 7
            dict['_2'] = 'Ajustes a los Débitos Fiscales de Periodos Anteriores'
            dict['_3'] = 0.00
            dict['_4'] = 0.00
            dict['_5'] = 0.00
            dict['_6'] = 0.00
            dict['_7'] = 0.00
            dict['_8'] = 0.00
            lista.append(dict)
            dict = OrderedDict()
            dict.update(dic)
            dict['_1'] = 8
            dict['_2'] = 'Total Ventas y Débitos Fiscales del Periodo'
            dict['_3'] = sum_tabla_fan['Total_Ventas_Exentas'] + sum_tabla_nd['Total_Ventas_Exentas'] + sum_tabla_fan['Imponible16'] + sum_tabla_nd['Imponible16'] + sum_tabla_fan['Imponible8'] + sum_tabla_nd['Imponible8']
            dict['_4'] = sum_tabla_fan['Impuesto16'] + sum_tabla_nd['Impuesto16'] + sum_tabla_fan['Impuesto8'] + sum_tabla_nd['Impuesto8']
            dict['_5'] = sum_tabla_nc['Total_Ventas_Exentas'] + sum_tabla_nc['Imponible16'] + sum_tabla_nc['Imponible8']
            dict['_6'] = sum_tabla_nc['Impuesto16'] + sum_tabla_nc['Impuesto8']
            dict['_7'] = sum_tabla_fan['Total_Ventas_Exentas'] + sum_tabla_nd['Total_Ventas_Exentas'] + sum_tabla_fan['Imponible16'] + sum_tabla_fan['Imponible8'] + sum_tabla_nd['Imponible16'] + sum_tabla_nd['Imponible8'] + sum_tabla_nc['Total_Ventas_Exentas'] + sum_tabla_nc['Imponible16'] + sum_tabla_nc['Imponible8']
            dict['_8'] = sum_tabla_fan['Impuesto16'] + sum_tabla_nd['Impuesto16'] + sum_tabla_nc['Impuesto16'] + sum_tabla_fan['Impuesto8'] + sum_tabla_nd['Impuesto8'] + sum_tabla_nc['Impuesto8']
            lista.append(dict)
            dict = OrderedDict()
            dict.update(dic)
            dict['_1'] = 9
            dict['_2'] = 'Total Retenciones'
            dict['_3'] = 0.00
            dict['_4'] = 0.00
            dict['_5'] = 0.00
            dict['_6'] = 0.00
            dict['_7'] = 0.00
            dict['_8'] = sum_tabla_fan['Retenciones'] + sum_tabla_nd['Retenciones'] + sum_tabla_nc['Retenciones']
            lista.append(dict)
            tabla = pd.DataFrame(lista)
        return tabla

    def _table_sale_book(self, wizard=False):
        if wizard:
            wiz = self.search([('id', '=', wizard)])
        else:
            wiz = self
        tabla1 = wiz._sale_book_invoice()
        union = pd.concat([tabla1])
        return union

    def _table_resumen_sale_book(self, wizard=False):
        if wizard:
            wiz = self.search([('id', '=', wizard)])
        else:
            wiz = self
        tabla1 = wiz._sale_book_invoice_resumen_excel()
        union = pd.concat([tabla1])
        return union
