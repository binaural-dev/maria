# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
_logger = logging.getLogger(__name__)

class StockWarehouseInvoiceStockMove(models.Model):
	_inherit = 'stock.warehouse'
	is_sale_storage = fields.Boolean(string='Es Almacen de ventas')