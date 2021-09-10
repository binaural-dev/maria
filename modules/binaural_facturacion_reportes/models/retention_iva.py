from openerp import models, fields, api, exceptions
from collections import OrderedDict
import pandas as pd
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)


class RetentionIvaReport(models.TransientModel):
    _inherit = 'wizard.retention.iva'

    def _retention_iva_excel(self):
        search_domain = self._get_domain()
        search_domain += [
            ('type', 'in', ['in_invoice']),
            ('type_retention', 'in', ['iva']),
            ('state', 'in', ['emitted']),
        ]
        docs = self.env['account.retention'].search(search_domain, order='id asc')
        dic = OrderedDict([
            ('Nro', 0),
            ('Año', ''),
            ('Mes', ''),
            ('Comprobante', ''),
            ('R.I.F', ''),
            ('Proveedor', ''),
            ('Nro. de Factura', ''),
            ('Nro. de Control', ''),
            ('Fecha de retención', ''),
            ('% de IVA', 0.00),
            ('IVA', 0.00),
            ('Total Factura', 0.00),
            ('% de retención', 0.00),
            ('Retenido', 0.00),
            ('Estatus', ''),


        ])
        lista = []
        op = 1
        for i in docs:
            for il in i.retention_line:
                dict = OrderedDict()
                dict.update(dic)
                dict['Nro'] = op
                dict['Año'] = str(i.date_accounting.year)
                dict['Mes'] = str(i.date_accounting.month)
                dict['Comprobante'] = i.number
                dict['R.I.F'] = i.partner_id.vat
                dict['Proveedor'] = i.partner_id.name
                dict['Nro. de Factura'] = il.invoice_id.name
                dict['Nro. de Control'] = il.invoice_id.correlative
                pi = str(i.date_accounting)
                fpi = datetime.strptime(pi, '%Y-%m-%d')
                dict['Fecha de retención'] = fpi.strftime('%d/%m/%Y')
                dict['% de IVA'] = il.tax_line/100
                dict['IVA'] = il.foreign_iva_amount
                dict['Total Factura'] = il.foreign_facture_total
                dict['% de retención'] = il.porcentage_retention/100
                dict['Retenido'] = il.foreign_retention_amount
                dict['Estatus'] = 'Emitida' if i.state == 'emitted' else ''
                
                lista.append(dict)
                op += 1
        tabla = pd.DataFrame(lista)
        return tabla

    def _table_retention_iva(self, wizard=False):
        if wizard:
            wiz = self.search([('id', '=', wizard)])
        else:
            wiz = self
        tabla1 = wiz._retention_iva_excel()
        union = pd.concat([tabla1])
        return union