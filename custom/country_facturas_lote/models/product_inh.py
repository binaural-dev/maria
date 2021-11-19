# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Country_Facturas_Lote_Product_Inh(models.Model):
	_inherit = 'product.template'

	fixed_concept = fields.Boolean(string='Concepto fijo')
