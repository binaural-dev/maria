# -*- coding: utf-8 -*-

from odoo import models, fields, api, http
from datetime import datetime, date
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


from collections import OrderedDict
import pandas as pd
import sys
from io import BytesIO
import logging
import time
import os
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception,content_disposition
import xlsxwriter
_logger = logging.getLogger(__name__)
class WizardAccountsPaymentCountrySociosReportes(models.TransientModel):
    _inherit = 'wizard.accounts.payment'
    
    #para uno en particular
    def _get_accounts_aging_for_supplier(self):
        list = []
        search = [] if self.today else self._get_domain()

        if self.type_report == 1:
            search += [('partner_id', '=', self.partner_id.id)]
            search += [('type', 'in', ['in_invoice', 'in_refund', 'in_debit','in_contingence'])]
            search += [('state', 'not in', ['draft', 'cancel', 'paid'])]
        else:
            search += [('partner_id', '=', self.customer_partner_id.id)]
            search += [('type', 'in', ['out_invoice', 'out_refund', 'out_debit','out_contingence'])]
            search += [('state', 'not in', ['cancel', 'paid'])]
        
        invoices = self.env['account.invoice'].search(search)
        columns = self.create_columns()
        for invoice in invoices:
            data = dict(oper='FACT' if invoice.type in ['in_invoice', 'out_invoice','out_contingence','in_contingence'] else 'NC' if invoice.type in ['in_refund', 'out_refund'] else 'ND',
                        date_invoice=datetime.strptime(str(invoice.date_invoice), '%Y-%m-%d').strftime('%d-%m-%Y'),
                        column_1=0, column_2=0, column_3=0, column_4=0, column_5=0,
                        residual=0, number=invoice.number, partner=invoice.partner_id.name)
            
            
            
            if invoice.type in ['out_refund', 'in_refund']:
                data['date_due']=datetime.strptime(str(invoice.date_due), '%Y-%m-%d').strftime('%d-%m-%Y')
                if invoice.days_expired <= columns[1]:
                    data['column_1'] -= invoice.residual
                elif columns[1] < invoice.days_expired <= columns[2]:
                    data['column_2'] -= invoice.residual
                elif columns[2] < invoice.days_expired <= columns[3]:
                    data['column_3'] -= invoice.residual
                elif columns[3] < invoice.days_expired <= columns[4]:
                    data['column_4'] -= invoice.residual
                elif columns[4] < invoice.days_expired:
                    data['column_5'] -= invoice.residual
                data['residual'] = -invoice.residual
            else:
                if invoice.state != 'draft':
                    days_expired = invoice.days_expired
                    data['date_due']=datetime.strptime(str(invoice.date_due), '%Y-%m-%d').strftime('%d-%m-%Y')

                else:
                    days_expired = self.calc_days_expired_draft(invoice)
                    #print("crete_date",invoice.create_date)
                    if invoice.fee_period:
                        data['date_due'] = datetime.strptime(str(invoice.fee_period), '%Y-%m-%d').strftime('%d-%m-%Y')
                    else:
                        data['date_due'] = datetime.strptime(str(invoice.create_date), '%Y-%m-%d').strftime('%d-%m-%Y')
                amount_due = invoice.residual if invoice.state != 'draft' else invoice.amount_total
                if days_expired <= columns[1]:
                    data['column_1'] += amount_due
                elif columns[1] < days_expired <= columns[2]:
                    data['column_2'] += amount_due
                elif columns[2] < days_expired <= columns[3]:
                    data['column_3'] += amount_due
                elif columns[3] < days_expired <= columns[4]:
                    data['column_4'] += amount_due
                elif columns[4] < days_expired:
                    data['column_5'] += amount_due
                data['residual'] = amount_due
            list.append(data)
        return list

    #para todos
    def _get_all_accounts_aging(self):
        list, columns = [], []
        if self.type_report == 1:
            partners = self.env['res.partner'].search(
                [('active', '=', True), ('supplier', '=', True)])
        else:
            partners = self.env['res.partner'].search(
                [('active', '=', True), ('customer', '=', True)])
        self._get_day_aging()
        columns = self.create_columns()

        for partner in partners:
            data = {
                'partner': partner.name,
                'column_1': 0,
                'column_2': 0,
                'column_3': 0,
                'column_4': 0,
                'column_5': 0,
                'days': 0,
                'residual': 0,
            }
            search = [] if self.today else self._get_domain()
            if self.type_report == 1:
                search += [('type', 'in', ['in_invoice', 'in_refund', 'in_debit','in_contingence'])]
                search += [('state', 'not in', ['draft', 'cancel', 'paid'])]
            else:
                search += [('type', 'in', ['out_invoice', 'out_refund', 'out_debit','out_contingence'])]
                search += [('state', 'not in', ['cancel', 'paid'])] #incluir borrador
            search += [('partner_id', '=', partner.id)]
            
            invoices_for_partner = self.env['account.invoice'].search(search)
            days = 0
            residual = 0

            if len(invoices_for_partner) != 0:
                for invoice in invoices_for_partner:
                    if invoice.state != 'draft':
                        days_expired = invoice.days_expired
                    else:
                        days_expired = self.calc_days_expired_draft(invoice)
                    days += days_expired
                    if invoice.type in ['out_refund', 'in_refund']:
                        residual -= invoice.residual
                        if invoice.days_expired <= columns[1]:
                            data['column_1'] -= invoice.residual
                        elif columns[1] < invoice.days_expired <= columns[2]:
                            data['column_2'] -= invoice.residual
                        elif columns[2] < invoice.days_expired <= columns[3]:
                            data['column_3'] -= invoice.residual
                        elif columns[3] < invoice.days_expired <= columns[4]:
                            data['column_4'] -= invoice.residual
                        elif columns[4] < invoice.days_expired:
                            data['column_5'] -= invoice.residual
                    else:
                        amount_due = invoice.residual if invoice.state != 'draft' else invoice.amount_total
                        residual += amount_due
                        if days_expired <= columns[1]:
                            data['column_1'] += amount_due
                        elif columns[1] < days_expired <= columns[2]:
                            data['column_2'] += amount_due
                        elif columns[2] < days_expired <= columns[3]:
                            data['column_3'] += amount_due
                        elif columns[3] < days_expired <= columns[4]:
                            data['column_4'] += amount_due
                        elif columns[4] < days_expired:
                            data['column_5'] += amount_due
                data['days'] = days / len(invoices_for_partner)
                data['residual'] = residual
            list.append(data)
        #print("lista retornada de la funcion",list)
        return list

    
    def calc_days_expired_draft(self,invoice):
        #fee_period
        days_expired = 0
        today = fields.Date.today()
        if invoice.fee_period:
            days_expired = (today - invoice.fee_period).days
        return days_expired

    def print_excel(self):
        #print("llamar endpoint de excel")
        if int(self.env['ir.config_parameter'].sudo().get_param('days_max')) != 0:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/get_analisis_excel?&wizard=%s' % (self.id),
                'target': 'self'
            }
        else:
            raise UserError("La configuración de dias maximos no encontrada, contactar al adminsitrador del sistema.")

    def get_tabla_data(self):
        #print("Esta es el id del wizard:",self)
        if self.all_partner or self.customer_all_partner:
            lista = self._get_all_accounts_aging()
            lista = list(filter(lambda score: score['days'] >0, lista))
        else:
            lista = self._get_accounts_aging_for_supplier()

        
        
        
        if len(lista) >0:
            tabla = pd.DataFrame(lista)#.sort_values(['Cedula'], ascending=[1])
            return tabla
        return False

    def _excel_file_analisis_format(self,tabla):
        #header_data = ['#','Tipo Doc','Cedula','Nombre del Beneficiario','Forma de pago','Cuenta','Monto Neto','Nro Doc/Factura']
        data2 = BytesIO()
        #date = 'Fecha: ' + str(time.strftime("%d/%m/%y"))
        workbook = xlsxwriter.Workbook(data2, {'in_memory': True})
        datos = tabla
        workbook.add_format({'bold': True})
        worksheet2 = workbook.add_worksheet('Analisis de vencimiento')

        worksheet2.set_column('A:Z', 20)
        #worksheet2.set_column('D:F', 10)
        #worksheet2.set_column('G:J', 30)
        columnas = list(datos.columns.values)
        columns2 = [{'header':r} for r in columnas]
        currency_format = workbook.add_format({'num_format': '#.#,0'})

        data = datos.values.tolist()
        last_column = len(columns2)-1
        last_row = len(data)+1
        header_format = workbook.add_format({'bold': True,
                                     'bottom': 2,
                                     })#'bg_color': '#7EF7D0'
        header_format.set_align('center')
        header_format.set_align('vcenter')
        header_format.set_border(1)
        company_name = self.env.user.company_id.name
         
        
        #fila columna
        #worksheet2.write(1, 3, "logo",header_format)
        #worksheet2.write(0,0, "Nombre de la empresa",header_format)
        #worksheet2.write(1,0, company_name,header_format)

        #worksheet2.write(6, 3, "Descripción del pago",header_format)
        #worksheet2.write(7, 3, "=Descripcion_NS",header_format)
        #worksheet2.write(2,0, "Cantidad de Registros",header_format)
        #worksheet2.write(3,0, str(nro_op),header_format)

        #worksheet2.write(0, 1, "RIF",header_format)
        #worksheet2.write(1,1, str(self.env.user.company_id.vat),header_format)
        #worksheet2.write(1, 0, date,header_format)

        #worksheet2.write(2, 1, "Lote",header_format)
        #worksheet2.write(3,1,config_macro.correlative_lote+1,header_format)
        #worksheet2.write(0,2, "Serial",header_format)
        #worksheet2.write(1,2,config_macro.correlative_serial+1,header_format)
        #worksheet2.write(2,2,"Cuenta",header_format)
        #worksheet2.write(3,2,config_macro.bank_account_number,header_format)
        #config_macro.write({'correlative_serial':config_macro.correlative_serial+1,'correlative_lote':config_macro.correlative_lote+1})
        cells = xlsxwriter.utility.xl_range(1,0,last_row+1,last_column+0)
        general_format = workbook.add_format({'num_format': '#,##0.00',})
        for record in columns2:
            if record.get("header") not in ['partner','days','date_due','date_invoice','oper']:
                record.update({'format': general_format})

  
        worksheet2.add_table(cells, {'data': data, 'total_row': 1, 'columns':columns2,'header_row': True,'style': 'Table Style Light 11'})

        total_format = workbook.add_format({'bold': True,
                                     'bottom': 2,
                                     'num_format': '#.#,0',
                                     })
        ##,###0.00
        total_format.set_align('center')
        total_format.set_align('vcenter')
        total_format.set_border(1)
        
        if self.all_partner or self.customer_all_partner:
            headers = ["Nombre"]
            headers+=self._get_column_name()
            headers+=(["Dias Promedio","Saldo Adeudado"])
            for idx, val in enumerate(headers):
                worksheet2.write(1,idx,val,header_format)
        else:
            headers = ["Tipo","Fecha"]
            headers+=self._get_column_name()
            #headers.append("Dias Promedio")
            headers+=(["Saldo Adeudado","Número","Nombre","Vencimiento"])
            for idx, val in enumerate(headers):
                worksheet2.write(1,idx,val,header_format)

        workbook.close()
        data2 = data2.getvalue()
        return data2




class wizard_controler_expiration_analisis(http.Controller):

    @http.route('/web/get_analisis_excel', type='http', auth="user")
    @serialize_exception
    def download_document(self,wizard,debug=0):
        filecontent = ''
        report_obj = request.env['wizard.accounts.payment']
        if wizard:
            wiz = report_obj.search([('id', '=', wizard)])
        else:
            wiz = report_obj
        #print("Esta es el id del wizard:",self)
        
        #print("llamar a tabla")
        format = '.xlsx'
        #nombre = 'PROVEEDORES'
        tabla = wiz.get_tabla_data()
        #print("tabla",tabla)
        if not tabla.empty:
            filecontent = wiz._excel_file_analisis_format(tabla)

        
        return request.make_response(filecontent,
        [('Content-Type', 'application/pdf'), ('Content-Length', len(filecontent)),
        ('Content-Disposition', content_disposition('Analisis_vencimiento'+format))])