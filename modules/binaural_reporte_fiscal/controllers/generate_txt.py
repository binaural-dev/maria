# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from io import BytesIO, StringIO


class GenerateTxt(http.Controller):

    @http.route('/web/binary/download_txt', type='http', auth='user')
    def download_txt(self, date_start, date_end, **kw):
        retention = request.env['account.retention'].search([('date', '>=', date_start), ('date', '<=', date_end),
                                                             ('state', '=', 'emitted'),('type_retention', '=', 'iva'), ('type', '=', 'in_invoice')])
        data = request.env['txt.wizard']
        tabla, lista = data._retention_iva(retention)
        f = StringIO()
        for l in lista:
            f.write(l.get('RIF del agente de retención') + "\t")
            f.write(str(l.get('Período impositivo')) + "\t")
            f.write(l.get('Fecha de factura') + "\t")
            f.write(l.get('Tipo de operación') + "\t")
            f.write(l.get('Tipo de documento') + "\t")
            f.write(l.get('RIF de proveedor') + "\t")
            f.write(str(l.get('Número de documento')) + "\t")
            f.write(l.get('Número de control') + "\t")
            f.write(str("{:.2f}".format(l.get('Monto total del documento'))) + "\t")
            f.write(str("{:.2f}".format(l.get('Base imponible'))) + "\t")
            f.write(str("{:.2f}".format(l.get('Monto del Iva Retenido'))) + "\t")
            f.write(str(l.get('Número del documento afectado')) + "\t")
            f.write(str(l.get('Número de comprobante de retención')) + "\t")
            f.write(str("{:.2f}".format(l.get('Monto exento del IVA'))) + "\t")
            f.write(str("{:.2f}".format(l.get('Alícuota'))) + "\t")
            f.write(l.get('Número de Expediente'))
            f.write("\n")
        f.flush()
        f.seek(0)
        return request.make_response(f, [('Content-Type', 'text/plain'),
                                         ('Content-Disposition', 'attachment; filename=retenciones_iva.txt')])