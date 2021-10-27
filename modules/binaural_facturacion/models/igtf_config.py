# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
class AccountIgtfConfigBinauralFacturacion(models.Model):
	_name = 'account.igtf.config'
	_rec_name = "destination_account_id"
	
	def get_company_def(self):
		return self.env.user.company_id
	
	company_id = fields.Many2one('res.company',default=get_company_def, string='Compañía', readonly=True)
	destination_account_id = fields.Many2one('account.account',string="Cuenta contable",domain=[('deprecated','=',False),('user_type_id.internal_group','=','expense')],required=True)

	active = fields.Boolean(default=True,string="Activo")
	_sql_constraints = [('code_company_uniq_advance', 'unique (destination_account_id, company_id, active)', 'La cuenta de contable debe ser unica por empresa.')]
