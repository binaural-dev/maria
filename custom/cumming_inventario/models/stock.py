# -*- coding: utf-8 -*-
from odoo import models,fields,api


class PatternReportStock(models.Model):
	_inherit = 'stock.quant'

	pattern_id  = fields.Many2one(related='product_id.pattern_id',
		string='Modelo', store=True, readonly=True)