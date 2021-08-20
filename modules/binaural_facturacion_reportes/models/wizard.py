from odoo import models, fields, api, http, exceptions, SUPERUSER_ID
from datetime import date
from dateutil.relativedelta import relativedelta
import xlsxwriter
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from io import BytesIO
import logging
from datetime import datetime
from collections import OrderedDict
_logger = logging.getLogger(__name__)
from odoo.http import request


class WizardAccountingReports(models.TransientModel):
    _name = 'wizard.accounting.reports'
    _description = 'Wizard reportes contables'

    report = fields.Selection([
        ('purchase','Libro de Compras'),
        ('sale','Libro de Ventas'),
        ('other','Resumen'),
        ], 'Tipo de informe', required=True)
    date_start = fields.Date('Fecha de inicio', default=date.today().replace(day=1))
    date_end = fields.Date('Fecha de termino', default=date.today().replace(day=1)+relativedelta(months=1, days=-1))
    file = fields.Binary(readonly=True)
    filename = fields.Char()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    type_report = fields.Selection([
        ('pdf', 'PDF'),
        ('excel', 'EXCEL'),
    ], 'Formato', required=True, default='excel')

    def download_format(self):
        ext = ''
        if self.report == 'purchase' and self.type_report == 'excel':
            ext = '.xlsx'
        if self.report == 'sale' and self.type_report == 'excel':
            ext = '.xlsx'
        return ext

    def det_columns(self):
        dic = OrderedDict()
        if self.report == 'purchase':
            #Encabezado de compras
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
                ('Total Compras incluye IVA', 0.00),
                ('Total Compras Exentas', 0.00),
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
        if self.report == 'sale':
            #Encabezado de ventas
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
        return dic

    def det_columns_resumen(self):
        dic = OrderedDict([
            ('_1', 0),
            ('_2', ''),
            ('_3', 0),
            ('_4', 0),
            ('_5', 0),
            ('_6', 0),
            ('_7', 0),
            ('_8', 0),
        ])
        return dic

    def download_report(self):
        if self.type_report == 'pdf':
            return 'PDF'
        else:
            return 'EXCEL'

    def generate_report(self):
        type_report = self.download_report()
        if type_report == 'PDF':
            return self.print_pdf()
        else:
            return self.imprimir_excel()

    def _get_domain(self):
        search_domain = []
        search_domain += [('company_id','=',self.company_id.id)]
        if self.report == 'purchase':
            search_domain += [('date', '>=', self.date_start)]
            search_domain += [('date', '<=', self.date_end)]
        else:
            search_domain += [('invoice_date', '>=', self.date_start)]
            search_domain += [('invoice_date', '<=', self.date_end)]
        return search_domain

    def print_pdf(self):
        return

    def imprimir_excel(self):
        report = self.report
        filecontent = ''
        report_obj = request.env['wizard.accounting.reports']
        if report == 'purchase':
            table = report_obj._table_shopping_book(self.id)
            name = 'Libro de Compras'
            start = str(self.date_start)
            end = str(self.date_end)
            table_resumen = report_obj._table_resumen_shopping_book(self.id)
        if report == 'sale':
            table = report_obj._table_sale_book(self.id)
            name = 'Libro de Ventas'
            start = str(self.date_start)
            end = str(self.date_end)
            table_resumen = report_obj._table_resumen_sale_book(self.id)
        if not table.empty and name:
            if report == 'purchase':
                filecontent = report_obj._excel_file_purchase(table, name, start, end, table_resumen)
            if report == 'sale':
                filecontent = report_obj._excel_file_sale(table, name, start, end, table_resumen)
        if not filecontent:
            print("\nAAAAAAAAAAAAAA\n")
            raise exceptions.Warning('No hay datos para mostrar en reporte')
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/get_excel?report=%s&wizard=%s&start=%s&end=%s' % (self.report, self.id, str(self.date_start), str(self.date_end)),
            'target': 'self'
        }

    def _excel_file_purchase(self, table, name, start, end, table_resumen):
        company = self.env['res.company'].search([], limit=1)
        data2 = BytesIO()
        workbook = xlsxwriter.Workbook(data2, {'in_memory': True, 'nan_inf_to_errors': True})
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'gray'})
        datos = table
        datos_resumen = table_resumen
        total_1 = 0.00
        total_2 = 0.00
        total_3 = 0.00
        total_4 = 0.00
        total_5 = 0.00
        total_6 = 0.00
        total_7 = 0.00
        range_start = 'Desde: ' + datetime.strptime(start, '%Y-%m-%d').strftime('%d/%m/%Y')
        range_end = 'Hasta: ' + datetime.strptime(end, '%Y-%m-%d').strftime('%d/%m/%Y')
        worksheet2 = workbook.add_worksheet(name)
        worksheet2.set_column('A:C', 20)
        worksheet2.set_column('D:D', 30)
        worksheet2.set_column('E:I', 20)
        worksheet2.set_column('J:J', 30)
        worksheet2.set_column('K:R', 20)
        worksheet2.set_column('S:T', 30)
        worksheet2.write('A1', company.name)
        worksheet2.write('A2', name)
        worksheet2.write('A3', company.vat)
        worksheet2.write('A4', range_start)
        worksheet2.write('A5', range_end)
        worksheet2.merge_range('L5:N5', 'COMPRAS INTERNAS ALÍCUOTA GENERAL', merge_format)
        worksheet2.merge_range('O5:Q5', 'COMPRAS INTERNAS ALÍCUOTA GENERAL', merge_format)
        worksheet2.write('A6', 'Nª de Ope')
        worksheet2.write('B6', 'Fecha')
        worksheet2.write('C6', 'R.I.F')
        worksheet2.write('D6', 'Nombre/Razón Social')
        worksheet2.write('E6', 'Tipo')
        worksheet2.write('F6', 'Nª de Doc')
        worksheet2.write('G6', 'Nª de Control')
        worksheet2.write('H6', 'Tipo Transacción')
        worksheet2.write('I6', 'Nª de Doc. Afectado')
        worksheet2.write('J6', 'Total Compras incluye IVA')
        worksheet2.write('K6', 'Total Compras Exentas')
        worksheet2.write('L6', 'Imponible')
        worksheet2.write('M6', '%')
        worksheet2.write('N6', 'Impuesto')
        worksheet2.write('O6', 'Imponible')
        worksheet2.write('P6', '%')
        worksheet2.write('Q6', 'Impuesto')
        worksheet2.write('R6', 'Retenciones')
        worksheet2.write('S6', 'Comprobante de Ret.')
        worksheet2.write('T6', 'Fecha de Comprobante')
        worksheet2.set_row(5, 20, merge_format)
        columnas = list(datos.columns.values)
        columnas_resumen = list(datos_resumen.columns.values)
        columns2 = [{'header': r} for r in columnas]
        columns2_resumen = [{'header': r} for r in columnas_resumen]
        columns2[0].update({'total_string': 'Total'})
        data = datos.values.tolist()
        data_resumen = datos_resumen.values.tolist()
        currency_format = workbook.add_format({'num_format': '#,###0.00'})
        porcent_format = workbook.add_format({'num_format': '#,###0.00" "%'})
        date_format = workbook.add_format()
        date_format.set_num_format('d-mmm-yy')  # Format string.
        col3 = len(columns2) - 1
        col2 = len(data) + 6
        for record in columns2[9:12]:
            record.update({'format': currency_format})
        for record in columns2[13:15]:
            record.update({'format': currency_format})
        for record in columns2[16:18]:
            record.update({'format': currency_format})
        for record in columns2[12:13]:
            record.update({'format': porcent_format})
        for record in columns2[15:16]:
            record.update({'format': porcent_format})
        for record in columns2[18:19]:
            record.update({'format': porcent_format})
        i = 0
        while i < len(data):
            total_1 += data[i][9]
            total_2 += data[i][10]
            total_3 += data[i][11]
            total_4 += data[i][13]
            total_5 += data[i][14]
            total_6 += data[i][16]
            total_7 += data[i][17]
            i += 1
        worksheet2.write_number(col2, 9, float(total_1), currency_format)
        worksheet2.write_number(col2, 10, float(total_2), currency_format)
        worksheet2.write_number(col2, 11, float(total_3), currency_format)
        worksheet2.write_number(col2, 13, float(total_4), currency_format)
        worksheet2.write_number(col2, 14, float(total_5), currency_format)
        worksheet2.write_number(col2, 16, float(total_6), currency_format)
        worksheet2.write_number(col2, 17, float(total_7), currency_format)
        cells = xlsxwriter.utility.xl_range(6, 0, col2, col3)
        worksheet2.add_table(cells, {'data': data, 'total_row': True, 'columns': columns2, 'header_row': False})
        encabezado = 4 + len(data) + 5
        detalle_enc = encabezado + 1
        col6 = detalle_enc
        col4 = len(columnas_resumen) - 1
        col5 = len(data) + 6 + 6 + len(data_resumen)
        for record in columns2_resumen[2:8]:
            record.update({'format': currency_format})
        cells_resumen = xlsxwriter.utility.xl_range(col6, 0, col5, col4)
        worksheet2.add_table(
            cells_resumen, {'data': data_resumen, 'total_row': True, 'columns': columns2_resumen, 'header_row': False})
        worksheet2.merge_range(str('A') + str(encabezado) + ':' + str('B') + str(encabezado), 'Resumen', merge_format)
        worksheet2.merge_range(str('C') + str(encabezado) + ':' + str('D') + str(encabezado),
                               'Facturas / Notas de Débito', merge_format)
        worksheet2.merge_range(str('E') + str(encabezado) + ':' + str('F') + str(encabezado), 'Notas de Crédito',
                               merge_format)
        worksheet2.merge_range(str('G') + str(encabezado) + ':' + str('H') + str(encabezado), 'Total Neto',
                               merge_format)
    
        worksheet2.write(str('A') + str(detalle_enc), '', merge_format)
        worksheet2.write(str('B') + str(detalle_enc), 'Créditos Fiscales',
                         merge_format)
        worksheet2.write(str('C') + str(detalle_enc), 'Base Imponible',
                         merge_format)
        worksheet2.write(str('D') + str(detalle_enc), 'Crédito Fiscal', merge_format)
        worksheet2.write(str('E') + str(detalle_enc), 'Base Imponible', merge_format)
        worksheet2.write(str('F') + str(detalle_enc), 'Crédito Fiscal',
                         merge_format)
        worksheet2.write(str('G') + str(detalle_enc), 'Base Imponible',
                         merge_format)
        worksheet2.write(str('H') + str(detalle_enc), 'Crédito Fiscal', merge_format)
    
        workbook.close()
        data2 = data2.getvalue()
        return data2

    def _excel_file_sale(self, table, name, start, end, table_resumen):
        company = self.env['res.company'].search([], limit=1)
        data2 = BytesIO()
        workbook = xlsxwriter.Workbook(data2, {'in_memory': True,'nan_inf_to_errors': True})
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': 'gray'})
        datos = table
        datos_resumen = table_resumen
        total_1 = 0.00
        total_2 = 0.00
        total_3 = 0.00
        total_4 = 0.00
        total_5 = 0.00
        total_6 = 0.00
        total_7 = 0.00
        range_start = 'Desde: ' + datetime.strptime(start, '%Y-%m-%d').strftime('%d/%m/%Y')
        range_end = 'Hasta: ' + datetime.strptime(end, '%Y-%m-%d').strftime('%d/%m/%Y')
        worksheet2 = workbook.add_worksheet(name)
        worksheet2.set_column('A:C', 20)
        worksheet2.set_column('D:D', 30)
        worksheet2.set_column('E:I', 20)
        worksheet2.set_column('J:J', 30)
        worksheet2.set_column('K:R', 20)
        worksheet2.set_column('S:T', 30)
        worksheet2.write('A1', company.name)
        worksheet2.write('A2', name)
        worksheet2.write('A3', company.vat)
        worksheet2.write('A4', range_start)
        worksheet2.write('A5', range_end)
        worksheet2.merge_range('L5:N5','VENTAS INTERNAS ALÍCUOTA GENERAL', merge_format)
        worksheet2.merge_range('O5:Q5','VENTAS INTERNAS ALÍCUOTA GENERAL', merge_format)
        worksheet2.write('A6', 'Nª de Ope')
        worksheet2.write('B6', 'Fecha')
        worksheet2.write('C6', 'R.I.F')
        worksheet2.write('D6', 'Nombre/Razón Social')
        worksheet2.write('E6', 'Tipo')
        worksheet2.write('F6', 'Nª de Doc')
        worksheet2.write('G6', 'Nª de Control')
        worksheet2.write('H6', 'Tipo Transacción')
        worksheet2.write('I6', 'Nª de Doc. Afectado')
        worksheet2.write('J6', 'Total Ventas incluye IVA')
        worksheet2.write('K6', 'Total Ventas Exentas')
        worksheet2.write('L6', 'Imponible')
        worksheet2.write('M6', '%')
        worksheet2.write('N6', 'Impuesto')
        worksheet2.write('O6', 'Imponible')
        worksheet2.write('P6', '%')
        worksheet2.write('Q6', 'Impuesto')
        worksheet2.write('R6', 'Retenciones')
        worksheet2.write('S6', 'Comprobante de Ret.')
        worksheet2.write('T6', 'Fecha de Comprobante')
        worksheet2.set_row(5, 20, merge_format)
        columnas = list(datos.columns.values)
        columnas_resumen = list(datos_resumen.columns.values)
        columns2 = [{'header': r} for r in columnas]
        columns2_resumen = [{'header': r} for r in columnas_resumen]
        columns2[0].update({'total_string': 'Total'})
        data = datos.values.tolist()
        data_resumen = datos_resumen.values.tolist()
        currency_format = workbook.add_format({'num_format': '#,###0.00'})
        porcent_format = workbook.add_format({'num_format': '#,###0.00" "%'})
        date_format = workbook.add_format()
        date_format.set_num_format('d-mmm-yy')  # Format string.
        col3 = len(columns2) - 1
        col2 = len(data) + 6
        for record in columns2[9:12]:
            record.update({'format': currency_format})
        for record in columns2[13:15]:
            record.update({'format': currency_format})
        for record in columns2[16:18]:
            record.update({'format': currency_format})
        for record in columns2[12:13]:
            record.update({'format': porcent_format})
        for record in columns2[15:16]:
            record.update({'format': porcent_format})
        for record in columns2[18:19]:
            record.update({'format': porcent_format})
        i = 0
        while i < len(data):
            total_1 += data[i][9]
            total_2 += data[i][10]
            total_3 += data[i][11]
            total_4 += data[i][13]
            total_5 += data[i][14]
            total_6 += data[i][16]
            total_7 += data[i][17]
            i += 1
        worksheet2.write_number(col2, 9, float(total_1), currency_format)
        worksheet2.write_number(col2, 10, float(total_2), currency_format)
        worksheet2.write_number(col2, 11, float(total_3), currency_format)
        worksheet2.write_number(col2, 13, float(total_4), currency_format)
        worksheet2.write_number(col2, 14, float(total_5), currency_format)
        worksheet2.write_number(col2, 16, float(total_6), currency_format)
        worksheet2.write_number(col2, 17, float(total_7), currency_format)
        cells = xlsxwriter.utility.xl_range(6, 0, col2, col3)
        worksheet2.add_table(cells, {'data': data, 'total_row': True, 'columns': columns2, 'header_row': False})
        encabezado = 4 + len(data) + 5
        detalle_enc = encabezado + 1
        col6 = detalle_enc
        col4 = len(columnas_resumen) - 1
        col5 = len(data) + 6 + 6 + len(data_resumen)
        for record in columns2_resumen[2:8]:
            record.update({'format': currency_format})
        cells_resumen = xlsxwriter.utility.xl_range(col6, 0, col5, col4)
        worksheet2.add_table(
            cells_resumen, {'data': data_resumen, 'total_row': True, 'columns': columns2_resumen, 'header_row': False})
        worksheet2.merge_range(str('A') + str(encabezado) + ':' + str('B') + str(encabezado), 'Resumen', merge_format)
        worksheet2.merge_range(str('C') + str(encabezado) + ':' + str('D') + str(encabezado),
                               'Facturas / Notas de Débito', merge_format)
        worksheet2.merge_range(str('E') + str(encabezado) + ':' + str('F') + str(encabezado), 'Notas de Crédito',
                               merge_format)
        worksheet2.merge_range(str('G') + str(encabezado) + ':' + str('H') + str(encabezado), 'Total Neto',
                               merge_format)

        worksheet2.write(str('A') + str(detalle_enc), '', merge_format)
        worksheet2.write(str('B') + str(detalle_enc), 'Débitos Fiscales',
                         merge_format)
        worksheet2.write(str('C') + str(detalle_enc), 'Base Imponible',
                         merge_format)
        worksheet2.write(str('D') + str(detalle_enc), 'Débito Fiscal', merge_format)
        worksheet2.write(str('E') + str(detalle_enc), 'Base Imponible', merge_format)
        worksheet2.write(str('F') + str(detalle_enc), 'Débito Fiscal',
                         merge_format)
        worksheet2.write(str('G') + str(detalle_enc), 'Base Imponible',
                         merge_format)
        worksheet2.write(str('H') + str(detalle_enc), 'Débito Fiscal', merge_format)
        
        workbook.close()
        data2 = data2.getvalue()
        return data2


class WizardAccountingReportsExcel(models.TransientModel):
    _name = 'wizard.accounting.reports.excel'
    _description = 'Formato excel reportes contables'

    file = fields.Binary()
    filename = fields.Char()


class AccountingReportsController(http.Controller):

    @http.route('/web/get_excel', type='http', auth="user")
    @serialize_exception
    def download_document(self, report, wizard, start, end):
        report = report
        filecontent = ''
        if report in ['purchase', 'sale', 'other']:
            report_obj = request.env['wizard.accounting.reports']
        if report == 'purchase':
            table = report_obj._table_shopping_book(int(wizard))
            name = 'Libro de Compras'
            start = start
            end = end
            table_resumen = report_obj._table_resumen_shopping_book(int(wizard))
        if report == 'sale':
            table = report_obj._table_sale_book(int(wizard))
            name = 'Libro de Ventas'
            table_resumen = report_obj._table_resumen_sale_book(int(wizard))
        if report == 'other':
            raise exceptions.Warning('Reporte no establecido')
        if not table.empty and name:
            if report == 'purchase':
                filecontent = report_obj._excel_file_purchase(table, name, start, end, table_resumen)
            if report == 'sale':
                filecontent = report_obj._excel_file_sale(table, name, start, end, table_resumen)
        if not filecontent:
            print("noy filecontent")
            report_obj.imprimir_excel(int(wizard))
            return
        format = '.xlsx'
        return request.make_response(filecontent,
        [('Content-Type', 'application/pdf'), ('Content-Length', len(filecontent)),
        ('Content-Disposition', content_disposition(name+format))])