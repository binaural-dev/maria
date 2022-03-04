from openerp import models, fields, api, exceptions
from collections import OrderedDict
import pandas as pd
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)


class RetentionIslrReport(models.TransientModel):
	_inherit = 'wizard.retention.islr'

	def _retention_islr_excel(self):
		foreign_currency_id = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
		search_domain = self._get_domain()
		search_domain += [
			('type', 'in', ['in_invoice']),
            ('type_retention', 'in', ['islr']),
			('state', 'in', ['emitted']),
		]
		docs = self.env['account.retention'].search(search_domain, order='id asc')
		dic = OrderedDict([
			('ID Sec', 0),
			('RIF Retenido', ''),
			('Número factura', ''),
			('Control Número', ''),
			('Fecha Operación', ''),
			('Código Concepto', ''),
			('Monto Operación', 0.00),
			('Porcentaje de retención', 0.00),


		])
		lista = []
		op = 1
		for i in docs:
			for il in i.retention_line:
				dict = OrderedDict()
				dict.update(dic)
				dict['ID Sec'] = op
				dict['RIF Retenido'] = i.partner_id.prefix_vat + i.partner_id.vat
				nf = ''
				pi = str(i.date_accounting)
				fpi = datetime.strptime(pi, '%Y-%m-%d')
				"""if i.islr_line_ids:
					for x in i.islr_line_ids:
						if x.invoice_id.name:
							nf += '-'
							nf += x.invoice_id.name"""
				if len(il.invoice_id.name)>10:
					dict['Número factura'] = il.invoice_id.name[-10:]
				else:
					dict['Número factura'] = il.invoice_id.name
				dict['Control Número'] = il.invoice_id.correlative
				dict['Fecha Operación'] = fpi.strftime('%d/%m/%Y')
				concept = ''
				alicuota = ''
				for x in il.payment_concept_id.line_payment_concept_ids:
					if x.type_person_ids.name == i.partner_id.type_person_ids.name:
						concept = x.code
						#alicuota = x.percentage_tax_base
						alicuota = x.tariffs_ids.percentage if x.tariffs_ids else ''
						break
				dict['Código Concepto'] = concept
				#dict['Monto Operación'] = i.islr_line_ids[0].invoice_id.amount_total
				dict['Monto Operación'] = il.foreign_facture_amount if foreign_currency_id == 3 else il.facture_amount
				dict['Porcentaje de retención'] = alicuota
				lista.append(dict)
				op += 1
		tabla = pd.DataFrame(lista)
		return tabla

	def _table_retention_islr(self, wizard=False):
		if wizard:
			wiz = self.search([('id', '=', wizard)])
		else:
			wiz = self
		tabla1 = wiz._retention_islr_excel()
		union = pd.concat([tabla1])
		return union