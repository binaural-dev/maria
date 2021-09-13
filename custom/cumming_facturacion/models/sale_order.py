# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class SaleOrderMaxCam(models.Model):
	_inherit = 'sale.order'


	@api.constrains('amount_total','payment_term_id')
	def _onchange_limit_credit(self):
		for record in self:
			_logger.info("record.payment_term_id %s",record.payment_term_id)
			_logger.info("record.env.ref('account.account_payment_term_immediate') %s",record.env.ref('account.account_payment_term_immediate'))
			_logger.info("record.partner_id.credit_limit %s",record.partner_id.credit_limit)
			record.ensure_one()
			if record.state in ['draft', 'sent'] and record.partner_id.credit_limit > 0 and record.payment_term_id != record.env.ref('account.account_payment_term_immediate'):
				due = record.partner_id.total_due + record.amount_total
				if due > record.partner_id.credit_limit:
					raise UserError(_("El cliente no tiene un límite de crédito disponible"))
				

	def action_confirm(self):
		exception = False
		product_ids = []
		for record in self:
			due = record.partner_id.total_due + record.amount_total
			if due > record.partner_id.credit_limit and record.partner_id.credit_limit > 0 and record.payment_term_id != record.env.ref('account.account_payment_term_immediate'):
				raise UserError(_("El cliente no tiene un límite de crédito disponible"))
		res = super(SaleOrderMaxCam, self).action_confirm()
		return res

	@api.onchange('order_line')
	def no_duplicate_product_id(self):
		product_ids = []
		for line in self.order_line:
			if line.product_id.id in product_ids:
				raise UserError(_("no puede agregar un producto que ya fué agregado"))
			else:
				product_ids.append(line.product_id.id)

	@api.constrains('order_line')
	def _constrains_product_id(self):
		product_ids = []
		for line in self.order_line:
			if line.product_id.id in product_ids:
				raise UserError(_("no puede agregar un producto que ya fué agregado"))
			else:
				product_ids.append(line.product_id.id)

	def sync_lines(self):
		lines_without_invoice_lines = self.env['sale.order.line'].sudo().search([('invoice_lines','=',False),('state','in',['sale','done'])])
		orders = []
		for l in lines_without_invoice_lines:
			if l.order_id.name not in orders:
				orders.append(l.order_id.name)
		_logger.info("Cantidad de ordenes con lineas sin factura y que si estan confirmadas aun no se si esten como origen de factura %s",len(orders))
		orders_sale = []
		for o in orders:
			invoices = []
			inv = self.env['account.move'].sudo().search([('invoice_origin','=',o)])

			if inv:
				for i in inv:
					invoices.append(i.id)
			if len(invoices)>0:
				orders_sale.append({'order':o,'invoices':invoices})
		
		_logger.info("este es el resultado de las ordenes que no tienen lineas de factura asociada, pero si son origen de facturas %s",orders_sale)
		_logger.info("este es el resultado de las ordenes que no tienen lineas de factura asociada, pero si son origen de facturas %s",len(orders_sale))
		for orden in orders_sale:
			orden_obj = self.env['sale.order'].sudo().search([('name','=',orden.get("order",False))],limit=1)
			if orden_obj:
				for factura in orden.get('invoices',[]):
					factura_obj = self.env['account.move'].sudo().browse(int(factura))
					if factura_obj:
						for linea_factura in factura_obj.invoice_line_ids:
							for linea_pedido in orden_obj.order_line:
								if linea_factura.product_id.id == linea_pedido.product_id.id:
									#_logger.info("las lineas coinciden (al menos el producto es el mismo)")
									linea_factura.write({'sale_line_ids': [(4, linea_pedido.id)]})
									linea_pedido.write({'invoice_lines':[(4, linea_factura.id)]})


class SaleOrderLineMaxCam(models.Model):
	_inherit = 'sale.order.line'

	def _action_launch_stock_rule(self, previous_product_uom_qty=False):
		"""
		Launch procurement group run method with required/custom fields genrated by a
		sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
		depending on the sale order line product rule.
		"""
		_logger.info("DISPARO ACTION LAUNCH RULE")
		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
		procurements = []
		output = []
		cont = 0
		cont_all = 0
		lista_items = []
		qty_lines = int(self.env['ir.config_parameter'].sudo().get_param('qty_max'))
		if not qty_lines:
			qty_lines = 15
		for item in self:
			if cont < qty_lines:
				lista_items.append(item)
				cont += 1
				cont_all += 1

			if cont == qty_lines or len(self) == cont_all:
				output.append(lista_items)
				cont = 0
				lista_items = []
		for s in output:
			group_id = False
			procurements = []
			for line in s:  # self
				line = line.with_company(line.company_id)
				if line.state != 'sale' or not line.product_id.type in ('consu', 'product'):
					continue
				qty = line._get_qty_procurement(previous_product_uom_qty)
				if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
					continue

				# group_id = line._get_procurement_group()

				if not group_id:
					group_id = self.env['procurement.group'].sudo().create(line._prepare_procurement_group_vals())
					line.order_id.procurement_group_id = group_id
				else:
					# In case the procurement group is already created and the order was
					# cancelled, we need to update certain values of the group.
					updated_vals = {}
					if group_id.partner_id != line.order_id.partner_shipping_id:
						updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
					if group_id.move_type != line.order_id.picking_policy:
						updated_vals.update({'move_type': line.order_id.picking_policy})
					if updated_vals:
						group_id.write(updated_vals)

				values = line._prepare_procurement_values(group_id=group_id)
				product_qty = line.product_uom_qty - qty

				line_uom = line.product_uom
				quant_uom = line.product_id.uom_id
				product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
				procurements.append(self.env['procurement.group'].sudo().Procurement(
					line.product_id, product_qty, procurement_uom,
					line.order_id.partner_shipping_id.property_stock_customer,
					line.name, line.order_id.name, line.order_id.company_id, values))
			if procurements:
				self.env['procurement.group'].sudo().run(procurements)
		#codigo del procurement jit ejecutar de una vez aqui para no usar super
		orders = list(set(x.order_id for x in self))
		for order in orders:
		 	reassign = order.picking_ids.filtered(
		 		lambda x: x.state == 'confirmed' or (x.state in ['waiting', 'assigned'] and not x.printed))
		 	if reassign:
		 		# Trigger the Scheduler for Pickings
		 		reassign.sudo().action_confirm()
		 		reassign.sudo().action_assign()
		return True

		#return super(SaleOrderLineMaxCam, self)._action_launch_stock_rule(previous_product_uom_qty)
