# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

class SaleOrderInvoiceStockMove(models.Model):
	_inherit = 'sale.order'

	force_picking_invoice_stock = fields.Boolean(string='Generar orden de inventario')

class SaleOrderLineInvoiceStockMove(models.Model):
	_inherit = 'sale.order.line'

	force_picking_invoice_stock = fields.Boolean(string='Generar orden de inventario',related='order_id.force_picking_invoice_stock')

	def _action_launch_stock_rule(self, previous_product_uom_qty=False):
		_logger.info("Lunch stock000000000000000000000000000000000000000000000000000000000000000000000000")
		"""Si tiene activa la opcion de picking desde pedido ejecutar la funcion o el pedido de venta tiene marcada la opcion de generar el picking"""
		if self.env['ir.config_parameter'].sudo().get_param('picking_from_sale_orer') or any(l.force_picking_invoice_stock for l in self):
			return super(SaleOrderLineInvoiceStockMove, self)._action_launch_stock_rule(previous_product_uom_qty)
		return True

