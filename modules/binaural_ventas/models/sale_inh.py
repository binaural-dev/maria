# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from werkzeug.urls import url_encode
import logging
_logger = logging.getLogger(__name__)


class SaleOrderBinauralVentas(models.Model):
	_inherit = 'sale.order'
	
	def recalculate_foreign_rate(self):
		for record in self:
			record._compute_foreign_currency_rate()
	
	@api.onchange('filter_partner')
	def get_domain_partner(self):
		for record in self:
			record.partner_id = False
			if record.filter_partner == 'customer':
				return {'domain': {
					'partner_id': [('customer_rank', '>=', 1)],
				}}
			elif record.filter_partner == 'supplier':
				return {'domain': {
					'partner_id': [('supplier_rank', '>=', 1)],
				}}
			elif record.filter_partner == 'contact':
				return {'domain': {
					'partner_id': [('supplier_rank', '=', 0), ('customer_rank', '=', 0)],
				}}
			else:
				return []
	
	def default_alternate_currency(self):
		alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
		
		if alternate_currency:
			return alternate_currency
		else:
			return False

	@api.model
	def _get_conversion_rate_purchase(self, from_currency, to_currency, order):
		from_currency = from_currency.with_env(self.env)
		to_currency = to_currency.with_env(self.env)
		rate_before = self.env['res.currency.rate'].search([('currency_id', '=', from_currency.id),
															('name', '<=', order.date_planned)], limit=1,
														   order='id desc')
		rate_from = None
		if rate_before:
			rate_from = rate_before
		else:
			rate_after = self.env['res.currency.rate'].search([('currency_id', '=', from_currency.id),
															   ('name', '>=', order.date_planned)], limit=1,
															  order='id asc')
			if rate_after:
				rate_from = rate_after
		return to_currency.rate / (rate_from.rate if rate_from else from_currency.rate)

	@api.onchange('foreign_currency_id', 'foreign_currency_date')
	def _compute_foreign_currency_rate(self):
		for record in self:
			rate = self.env['res.currency.rate'].search([('currency_id', '=', record.foreign_currency_id.id),
																('name', '<=', record.foreign_currency_date)], limit=1,
															   order='name desc')
			if rate:
				record.update({
					'foreign_currency_rate': rate.rate,
				})
			else:
				rate = self.env['res.currency.rate'].search([('currency_id', '=', record.foreign_currency_id.id),
																   ('name', '>=', record.foreign_currency_date)], limit=1,
																  order='name asc')
				if rate:
					record.update({
						'foreign_currency_rate': rate.rate,
					})
				else:
					record.update({
						'foreign_currency_rate': 0.00,
					})

	@api.depends('order_line.price_total', 'foreign_currency_rate')
	def _amount_all_foreign(self):
		"""
		Compute the foreign total amounts of the SO.
		"""
		for order in self:
			foreign_amount_untaxed = foreign_amount_tax = 0.0
			for line in order.order_line:
				foreign_amount_untaxed += line.price_subtotal
				foreign_amount_tax += line.price_tax
			foreign_amount_untaxed *= order.foreign_currency_rate
			foreign_amount_tax *= order.foreign_currency_rate
			order.update({
				'foreign_amount_untaxed': foreign_amount_untaxed,
				'foreign_amount_tax': foreign_amount_tax,
				'foreign_amount_total': foreign_amount_untaxed + foreign_amount_tax,
			})
	@api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.tax_id', 'partner_id', 'currency_id')
	def _foreign_amount_by_group(self):
		
		for order in self:
			currency = order.currency_id or order.company_id.currency_id
			fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
			res = {}
			for line in order.order_line:
				price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
				taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id,
												partner=order.partner_shipping_id)['taxes']
				for tax in line.tax_id:
					group = tax.tax_group_id
					res.setdefault(group, {'amount': 0.0, 'base': 0.0})
					for t in taxes:
						if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
							res[group]['amount'] += t['amount'] * order.foreign_currency_rate
							res[group]['base'] += t['base'] * order.foreign_currency_rate
			_logger.info("res========== %s",res)
			res = sorted(res.items(), key=lambda l: l[0].sequence)
			order.foreign_amount_by_group = [(
				l[0].name, l[1]['amount'], l[1]['base'],
				fmt(l[1]['amount']), fmt(l[1]['base']),
				len(res),
			) for l in res]
		
	phone = fields.Char(string='Teléfono', related='partner_id.phone')
	vat = fields.Char(string='RIF', compute='_get_vat')
	address = fields.Char(string='Dirección', related='partner_id.street')
	business_name = fields.Char(string='Razón Social', related='partner_id.business_name')
	
	amount_by_group = fields.Binary(string="Tax amount by group",compute='_compute_invoice_taxes_by_group',help='Edit Tax amounts if you encounter rounding issues.')
	partner_id = fields.Many2one(
		'res.partner', string='Customer', readonly=True,
		states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
		required=True, change_default=True, index=True, tracking=1)
	filter_partner = fields.Selection([('customer', 'Clientes'), ('supplier', 'Proveedores'), ('contact', 'Contactos')],\
									  string='Filtro de Contacto', default='customer')
	
	amount_by_group_base = fields.Binary(string="Tax amount by group",compute='_compute_invoice_taxes_by_group',help='Edit Tax amounts if you encounter rounding issues.')

	company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
		readonly=True, store=True,
		help='Utility field to express amount currency')
	# Foreing cyrrency fields
	foreign_currency_id = fields.Many2one('res.currency', default=default_alternate_currency,
										  tracking=True)
	foreign_currency_rate = fields.Float(string="Tasa", tracking=True)
	foreign_currency_date = fields.Date(string="Fecha", default=fields.Date.today(), tracking=True)

	foreign_amount_untaxed = fields.Monetary(string='Base Imponible', store=True, readonly=True, compute='_amount_all_foreign',
									 tracking=5)
	foreign_amount_tax = fields.Monetary(string='Impuestos', store=True, readonly=True, compute='_amount_all_foreign')
	foreign_amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all_foreign', tracking=4)
	foreign_amount_by_group = fields.Binary(string="Monto de impuesto por grupo", compute='_foreign_amount_by_group')


	def _inverse_foreign_currency_rate(self):
		for record in self:
			record.foreign_currency_rate = record.foreign_currency_rate

	@api.depends('partner_id')
	def _get_vat(self):
		for p in self:
			if p.partner_id.prefix_vat and p.partner_id.vat:
				vat = str(p.partner_id.prefix_vat) + str(p.partner_id.vat)
			else:
				vat = str(p.partner_id.vat)
			p.vat = vat.upper()

	@api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.tax_id', 'partner_id', 'currency_id')
	def _compute_invoice_taxes_by_group(self):
		''' Helper to get the taxes grouped according their account.tax.group.
		This method is only used when printing the invoice.
		'''
		_logger.info("se ejecuto la funcion:_compute_invoice_taxes_by_group")
		for move in self:
			lang_env = move.with_context(lang=move.partner_id.lang).env
			tax_lines = move.order_line.filtered(lambda line: line.tax_id)
			tax_balance_multiplicator = 1 #-1 if move.is_inbound(True) else 1
			res = {}
			# There are as many tax line as there are repartition lines
			done_taxes = set()
			for line in tax_lines:
				res.setdefault(line.tax_id.tax_group_id, {'base': 0.0, 'amount': 0.0})
				_logger.info("line.price_subtotal en primer for %s",line.price_subtotal)
				res[line.tax_id.tax_group_id]['base'] += tax_balance_multiplicator * (line.price_subtotal if line.currency_id else line.price_subtotal)
				tax_key_add_base = tuple(move._get_tax_key_for_group_add_base(line))
				_logger.info("done_taxesdone_taxes %s",done_taxes)

				if line.currency_id and line.company_currency_id and line.currency_id != line.company_currency_id:
					amount = line.company_currency_id._convert(line.price_tax, line.currency_id, line.company_id, line.order_id.date_order or fields.Date.context_today(self))
				else:
					amount = line.price_tax
				res[line.tax_id.tax_group_id]['amount'] += amount
				"""if tax_key_add_base not in done_taxes:
					_logger.info("line.price_tax en primer for %s",line.price_tax)
					if line.currency_id and line.company_currency_id and line.currency_id != line.company_currency_id:
						amount = line.company_currency_id._convert(line.price_tax, line.currency_id, line.company_id, line.date or fields.Date.context_today(self))
					else:
						amount = line.price_tax
					res[line.tax_id.tax_group_id]['amount'] += amount
					# The base should be added ONCE
					done_taxes.add(tax_key_add_base)"""

			# At this point we only want to keep the taxes with a zero amount since they do not
			# generate a tax line.
			zero_taxes = set()
			for line in move.order_line:
				for tax in line.tax_id.flatten_taxes_hierarchy():
					if tax.tax_group_id not in res or tax.tax_group_id in zero_taxes:
						res.setdefault(tax.tax_group_id, {'base': 0.0, 'amount': 0.0})
						res[tax.tax_group_id]['base'] += tax_balance_multiplicator * (line.price_subtotal if line.currency_id else line.price_subtotal)
						zero_taxes.add(tax.tax_group_id)

			_logger.info("res========== %s",res)

			res = sorted(res.items(), key=lambda l: l[0].sequence)
			move.amount_by_group = [(
				group.name, amounts['amount'],
				amounts['base'],
				formatLang(lang_env, amounts['amount'], currency_obj=move.currency_id),
				formatLang(lang_env, amounts['base'], currency_obj=move.currency_id),
				len(res),
				group.id
			) for group, amounts in res]

			move.amount_by_group_base = [(
				group.name.replace("IVA", "Total G").replace("TAX", "Total G"), amounts['base'],
				amounts['amount'],
				formatLang(lang_env, amounts['base'], currency_obj=move.currency_id),
				formatLang(lang_env, amounts['amount'], currency_obj=move.currency_id),
				len(res),
				group.id
			) for group, amounts in res]

	@api.model
	def _get_tax_key_for_group_add_base(self, line):
		"""
		Useful for _compute_invoice_taxes_by_group
		must be consistent with _get_tax_grouping_key_from_tax_line
		 @return list
		"""
		return [line.tax_id.id]

	def _create_invoices(self, grouped=False, final=False,date=None):
		"""
		Create the invoice associated to the SO.
		:param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
						(partner_invoice_id, currency)
		:param final: if True, refunds will be generated if necessary
		:returns: list of created invoices
		"""

		#qty lines by invoices
		qty_max = int(self.env['ir.config_parameter'].sudo().get_param('qty_max'))
		qty_lines = len(self.order_line)

		#si qty_max es 0 asignar por defecto 5 para que siempre deje facturar y las pruebas no fallen
		if qty_max == 0:
			qty_max = 5

		if qty_max and qty_max <= qty_lines:
			qty_invoice = qty_lines / qty_max
		else:
			qty_invoice = 1
		if (qty_invoice - int(qty_invoice)) > 0:
			qty_invoice = int(qty_invoice) + 1
		else:
			qty_invoice = int(qty_invoice)
		for i in range(0, qty_invoice):
			if not self.env['account.move'].check_access_rights('create', False):
				try:
					self.check_access_rights('write')
					self.check_access_rule('write')
				except AccessError:
					return self.env['account.move']

			# 1) Create invoices.
			invoice_vals_list = []
			invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
			for order in self:
				order = order.with_company(order.company_id)
				current_section_vals = None
				down_payments = order.env['sale.order.line']

				invoice_vals = order._prepare_invoice()
				invoiceable_lines = order._get_invoiceable_lines(final)

				if not any(not line.display_type for line in invoiceable_lines):
					raise self._nothing_to_invoice_error()

				invoice_line_vals = []
				down_payment_section_added = False
				for line in invoiceable_lines:
					#qty lines
					#set default qty_max_i para que en caso de que sea 0 igual deje facturar
					qty_max_i = int(self.env['ir.config_parameter'].sudo().get_param('qty_max'))
					if qty_max_i == 0:
						qty_max_i = 5

					if len(invoice_line_vals) < qty_max_i:
						if not down_payment_section_added and line.is_downpayment:
							# Create a dedicated section for the down payments
							# (put at the end of the invoiceable_lines)
							invoice_line_vals.append(
								(0, 0, order._prepare_down_payment_section_line(
									sequence=invoice_item_sequence,
								)),
							)
							dp_section = True
							invoice_item_sequence += 1
						invoice_line_vals.append(
							(0, 0, line._prepare_invoice_line(
								sequence=invoice_item_sequence,
							)),
						)
						invoice_item_sequence += 1

				invoice_vals['invoice_line_ids'] = invoice_line_vals
				invoice_vals_list.append(invoice_vals)

			if not invoice_vals_list:
				raise self._nothing_to_invoice_error()

			# 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
			if not grouped:
				new_invoice_vals_list = []
				invoice_grouping_keys = self._get_invoice_grouping_keys()
				for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
					origins = set()
					payment_refs = set()
					refs = set()
					ref_invoice_vals = None
					for invoice_vals in invoices:
						if not ref_invoice_vals:
							ref_invoice_vals = invoice_vals
						else:
							ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
						origins.add(invoice_vals['invoice_origin'])
						payment_refs.add(invoice_vals['payment_reference'])
						refs.add(invoice_vals['ref'])
					ref_invoice_vals.update({
						'ref': ', '.join(refs)[:2000],
						'invoice_origin': ', '.join(origins),
						'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
					})
					new_invoice_vals_list.append(ref_invoice_vals)
				invoice_vals_list = new_invoice_vals_list

			# 3) Create invoices.

			# As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
			# in a single invoice. Example:
			# SO 1:
			# - Section A (sequence: 10)
			# - Product A (sequence: 11)
			# SO 2:
			# - Section B (sequence: 10)
			# - Product B (sequence: 11)
			#
			# If SO 1 & 2 are grouped in the same invoice, the result will be:
			# - Section A (sequence: 10)
			# - Section B (sequence: 10)
			# - Product A (sequence: 11)
			# - Product B (sequence: 11)
			#
			# Resequencing should be safe, however we resequence only if there are less invoices than
			# orders, meaning a grouping might have been done. This could also mean that only a part
			# of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
			if len(invoice_vals_list) < len(self):
				SaleOrderLine = self.env['sale.order.line']
				for invoice in invoice_vals_list:
					sequence = 1
					for line in invoice['invoice_line_ids']:
						line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
						sequence += 1

			# Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
			# sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
			moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

			# 4) Some moves might actually be refunds: convert them if the total amount is negative
			# We do this after the moves have been created since we need taxes, etc. to know if the total
			# is actually negative or not
			if final:
				moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
			for move in moves:
				move.message_post_with_view('mail.message_origin_link',
					values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
					subtype_id=self.env.ref('mail.mt_note').id
				)
			return moves




class SaleOrderLineBinauralVentas(models.Model):
	_inherit = 'sale.order.line'

	def default_alternate_currency(self):
		alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
	
		if alternate_currency:
			return alternate_currency
		else:
			return False

	@api.depends('order_id.foreign_currency_rate')
	def _amount_all_foreign(self):
		"""
		Compute the foreign total amounts of the SO.
		"""
		for order in self:
			order.update({
				'foreign_price_unit': order.price_unit * order.order_id.foreign_currency_rate,
				'foreign_subtotal': order.price_subtotal * order.order_id.foreign_currency_rate,
			})
	
	company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
		readonly=True, store=True,
		help='Utility field to express amount currency')
	foreign_price_unit = fields.Monetary(string='Precio Alterno', store=True, readonly=True, compute='_amount_all_foreign', tracking=4)
	foreign_subtotal = fields.Monetary(string='Precio Alterno', store=True, readonly=True, compute='_amount_all_foreign', tracking=4)
	foreign_currency_id = fields.Many2one('res.currency', default=default_alternate_currency,
										  tracking=True)

class SaleAdvancePaymentInvBinaural(models.TransientModel):
	_inherit = "sale.advance.payment.inv"
	
	def create_invoices(self):
		_logger.info('Creando factura')
		sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
		_logger.info('Ordenes')
		_logger.info(sale_orders)
		qty_max = int(self.env['ir.config_parameter'].sudo().get_param('qty_max'))
		_logger.info('QTY_MAX')
		_logger.info(qty_max)
		qty_lines = 0
		for order in sale_orders:
			qty_lines = len(order.order_line)
		_logger.info('QTY_LINES')
		_logger.info(qty_lines)
		if qty_max and qty_max <= qty_lines:
			qty_invoice = qty_lines / qty_max
		else:
			qty_invoice = 1
		if (qty_invoice - int(qty_invoice)) > 0:
			qty_invoice = int(qty_invoice) + 1
		else:
			qty_invoice = int(qty_invoice)
		_logger.info('QTY_INVOICE')
		_logger.info(qty_invoice)
		for i in range(0, qty_invoice):
			if self.advance_payment_method == 'delivered':
				sale_orders._create_invoices(final=self.deduct_down_payments)
			else:
				# Create deposit product if necessary
				if not self.product_id:
					vals = self._prepare_deposit_product()
					self.product_id = self.env['product.product'].create(vals)
					self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id',
																	 self.product_id.id)
				
				sale_line_obj = self.env['sale.order.line']
				for order in sale_orders:
					amount, name = self._get_advance_details(order)
					
					if self.product_id.invoice_policy != 'order':
						raise UserError(_(
							'The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
					if self.product_id.type != 'service':
						raise UserError(_(
							"The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
					taxes = self.product_id.taxes_id.filtered(
						lambda r: not order.company_id or r.company_id == order.company_id)
					tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id, order.partner_shipping_id).ids
					analytic_tag_ids = []
					for line in order.order_line:
						analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
					
					so_line_values = self._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
					so_line = sale_line_obj.create(so_line_values)
					self._create_invoice(order, so_line, amount)
		if self._context.get('open_invoices', False):
			return sale_orders.action_view_invoice()
		return {'type': 'ir.actions.act_window_close'}