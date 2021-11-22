# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class ConfigJournalBatchInvoice(models.Model):
	_name = 'country.batch.invoice.config'
	_rec_name = "journal_id"

	def get_company_def(self):
		return self.env.user.company_id
	
	company_id = fields.Many2one('res.company', default=get_company_def, string='Compañía', readonly=True)
	active = fields.Boolean(default=True, string="Activo")
	journal_id = fields.Many2one('account.journal',string="Diario de factura",domain="[('type', '=', 'sale')]")
