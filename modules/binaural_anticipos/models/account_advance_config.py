# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class account_payment_bin_config(models.Model):
	_name = 'account.payment.config.advance'
	_rec_name = "advance_account_id"
	
	def get_company_def(self):
		return self.env.user.company_id
	
	company_id = fields.Many2one('res.company',default=get_company_def, string='Compañía', readonly=True)
	advance_account_id = fields.Many2one('account.account',string="Cuenta contable",domain=[('deprecated','=',False)],required=True)
	advance_type = fields.Selection([
			('customer', 'Cliente'),
			('supplier', 'Proveedor')],string="Tipo de anticipo",required=True)
	active = fields.Boolean(default=True,string="Activo")
	_sql_constraints = [
		('code_company_uniq_advance', 'unique (advance_account_id, advance_type, company_id, active)', 'La cuenta de anticipo debe ser unica.'),
	]
