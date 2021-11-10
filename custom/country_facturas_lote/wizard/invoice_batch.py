# -*- coding: utf-8 -*-

from odoo import api, fields, exceptions, http, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import xlsxwriter

from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from io import BytesIO
import logging
import time

from collections import OrderedDict
import pandas as pd

_logger = logging.getLogger(__name__)


class WizardInvoiceBatch(models.TransientModel):
	_name = "wizard.invoice.batch"
	_rec_name = "comment"
	
	def default_alternate_currency(self):
		alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))

		if alternate_currency:
			return alternate_currency
		else:
			return False

	company_id = fields.Many2one(
		'res.company', string='Compañía', default=lambda self: self.env.user.company_id)

	subscription_product_line_ids = fields.One2many(
				'wizard.invoice.batch.lines',
				'subscription_product_line_id',
				string="Lineas de factura",required=True
				)
	partners_ids = fields.Many2many(
		'res.partner', string='Socios', required=True, domain=[('active', '=', True)])#('customer', '=', True),

	sub_amount_untaxed = fields.Monetary(
		string='Exento',
		store=True,
		readonly=True,
		compute='_subscription_product_amount_all',
		track_visibility='always'
	)
	sub_amount_tax = fields.Monetary(
		string='Impuestos',
		store=True,
		readonly=True,
		compute='_subscription_product_amount_all',
		track_visibility='always'
	)
	sub_amount_total = fields.Monetary(
		string='Total',
		store=True,
		readonly=True,
		compute='_subscription_product_amount_all',
		track_visibility='always'
	)
	comment = fields.Text(string='Comentario')
	fee_period = fields.Date(string="Periodo de la cuota")

	foreign_currency_rate = fields.Float(string="Tasa", tracking=True)
	foreign_currency_date = fields.Date(string="Fecha", default=fields.Date.today(), tracking=True)

	foreign_currency_id = fields.Many2one('res.currency', default=default_alternate_currency,
										  tracking=True)
	currency_id = fields.Many2one(
		'res.currency',
		string="Moneda",
		default=lambda self: self.env.user.company_id.currency_id,
	)

	@api.onchange('foreign_currency_id', 'foreign_currency_date')
	def _compute_foreign_currency_rate(self):
		_logger.info("buscara tasa por defceto")
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

	def set_default_pricelist(self):
		p = self.env['product.pricelist'].search([('active','=',True)],limit=1).id
		return p
	
	pricelist_id = fields.Many2one('product.pricelist', string='Tarifas',default=set_default_pricelist)	
	
	#Generate invoice batch
	def generate_invoice_batch(self):
		invoice_id = self._recurring_create_invoice()
		if not self.partners_ids or not self.subscription_product_line_ids:
			raise UserError("Algunos campos obligatorios no fueron introducidos")
		if invoice_id and len(invoice_id) > 0:
			message_id = self.env['message.wizard'].create(
				{'message': _("Facturas generadas exitosamente.")})
			return {
				'name': _('Éxito'),
				'type': 'ir.actions.act_window',
				'view_mode': 'form',
				'res_model': 'message.wizard',
				# pass the id
				'res_id': message_id.id,
				'target': 'new'
			}
			"""base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			return {
				'name': _("Éxito"),
				'type': 'ir.actions.act_url',
				'url': base_url,
				'target': 'self',
			}"""
		#else:
		#	raise UserError("Algo no salio bien, error generando Facturas")
		#raise RedirectWarning(msg, action.id, _('Continuar'))
	@api.returns('account.move')
	def _recurring_create_invoice(self, automatic=False):
		AccountInvoice = self.env['account.move']
		invoices = []
		#automatic
		automatic = True
		for sub in self.partners_ids:
			#Solo country
			if not sub.action_number.number:
				raise UserError("Socio no posee numero de accion")
			#if not sub.business_name:
			#	raise UserError("Socio no posee razon social")
			if not sub.vat:
				raise UserError("Socio no posee rif o cedula")
			try:
				#buscar factura del mismo periodo
				already_invoiced = False
				prev_invoices = self.env['account.move'].sudo().search([('partner_id','=',sub.id),('move_type','=','out_invoice'),('state','!=','cancel')])
				if len(prev_invoices)>0:
					for prev_invoice in prev_invoices:
						if prev_invoice.fee_period:
							prev_month = prev_invoice.fee_period.month
							prev_year = prev_invoice.fee_period.year
							#si mes y a#o de periodos son iguales buscar si hay concepto fijo en la existente
							if self.fee_period.month == prev_month and self.fee_period.year == prev_year:
								#tiene factura con mismo periodo verificar si la cuota esta facturada si es si no hacer factura
								if any(line.product_id.fixed_concept for line in prev_invoice.invoice_line_ids):
									already_invoiced = True
									break
				if not already_invoiced:
					invoices.append(AccountInvoice.create(self._prepare_invoice(sub)))
					invoices[-1].message_post_with_view('mail.message_origin_link',
						values={'self': invoices[-1], 'origin': self},
						subtype_id=self.env.ref('mail.mt_note').id)
					invoices[-1]._onchange_recompute_dynamic_lines()
					invoices[-1]._compute_foreign_currency_rate()
				
				if automatic:
					self.env.cr.commit()
			except Exception as error:
				print("error interno")
				print(error)
				_logger.info("ERRORRRRRRRRRRRRRRRRRRR: %s",error)
				if automatic:
					self.env.cr.rollback()
					_logger.exception('Fail to create recurring invoice for partner %s', sub.name)
					raise UserError(error)
				else:
					raise UserError(error)
		return invoices
		

	def _prepare_invoice(self,partner):
		_logger.info("PARTNER A PASAR %s",partner)
		invoice = self._prepare_invoice_data_recurring(partner)
		invoice['invoice_line_ids'] = self._prepare_invoice_lines_recurring(invoice['fiscal_position_id'])
		return invoice
	
	def _prepare_invoice_data_recurring(self,p):
		self.ensure_one()
		
		if not p:
			raise UserError(_("Please select customer on contract subscription in order to create invoice.!"))
		company = self.company_id

		fpos_id = self.env['account.fiscal.position'].get_fiscal_position(p.id)
		#asignarlo por defecto arriba
		journal_config = self.env['country.batch.invoice.config'].search([('active','=',True)],limit=1)
		if journal_config and journal_config.journal_id:
			journal = journal_config.journal_id
		else:
			raise UserError(
				'No hay configuración registrada en el sistema por favor contacte al administrador')
			
		#comment = self.terms_and_conditions and  tools.html2plaintext(self.terms_and_conditions).strip() or ''
		
		return {
			#'name': p.business_name + ' name',
			#'origin': p.business_name + ' origin',
			'action_number': p.action_number.number,
			#'business_name': p.business_name,
			'vat': p.prefix_vat + p.vat,
			'address': p.street,
			#'related_project_id':self.id,
			#'account_id': p.property_account_receivable_id.id, 
			
			'partner_id': p.id,
			'currency_id': self.currency_id.id,
			'journal_id': journal.id,
			'invoice_date': fields.Date.today(),
			#'origin': self.code,
			'fiscal_position_id': fpos_id,
			'invoice_payment_term_id': p.property_payment_term_id.id,
			'company_id': company.id,
			# 'comment': _("This invoice covers the following period: %s - %s") % (next_date, end_date),
			'narration': self.comment,
			#'foreign_currency_rate':self.foreign_currency_rate,
			'move_type':'out_invoice',
			'fee_period':self.fee_period,
		}
	def _prepare_invoice_lines_recurring(self, fiscal_position):
		self.ensure_one()
		fiscal_position = self.env['account.fiscal.position'].browse(fiscal_position)
		return [(0, 0, self._prepare_invoice_line_recurring(line, fiscal_position)) for line in self.subscription_product_line_ids]
	
	def _prepare_invoice_line_recurring(self, line, fiscal_position):
		company = self.company_id


		account = line.product_id.property_account_income_id
		if not account:
			#account = line.product_id.categ_id.property_account_income_categ_id
			journal_config = self.env['country.batch.invoice.config'].search(
				[('active', '=', True)], limit=1)
			if journal_config and journal_config.journal_id:
				account = journal_config.journal_id.default_account_id
			else:
				raise UserError(
					'No hay configuración registrada en el sistema por favor contacte al administrador')
		account_id = fiscal_position.map_account(account).id

		#tax = line.product_id.taxes_id.filtered(lambda r: r.company_id == company)
		tax = line.tax_ids
		#tax = fiscal_position.map_tax(tax)
		return {
			'name': line.name,
			'account_id': account_id,
			'price_unit': line.price_unit or 0.0,
			'discount': line.discount,
			'quantity': line.product_uom_qty,
			#'uom_id': line.product_uom.id,
			'product_id': line.product_id.id,
			'tax_ids': [(6, 0, tax.ids)],
		}

	def action_subscription_invoice(self, invoice):
		list_i = []
		for i in invoice:
			list_i.append(i.id)
		if len(list_i) >0:
			action = self.env.ref('account.action_invoice_tree1').read()[0]
			action['domain'] = [('id', 'in', list_i)]
			return action
		else:
			return True



	@api.depends('subscription_product_line_ids.price_total')
	def _subscription_product_amount_all(self):
		"""
		Compute the total amounts of the SO.
		"""
		for rec in self:
			sub_amount_untaxed = sub_amount_tax = 0.0
			for line in rec.subscription_product_line_ids:
				sub_amount_untaxed += line.price_subtotal
				# FORWARDPORT UP TO 10.0
				if rec.company_id.tax_calculation_rounding_method == 'round_globally':
					price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
					taxes = line.tax_ids.compute_all(price, line.subscription_product_line_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.subscription_product_line_id.partner_id)
					sub_amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
				else:
					sub_amount_tax += line.price_tax
			rec.update({
				'sub_amount_untaxed': rec.company_id.currency_id.round(sub_amount_untaxed),
				'sub_amount_tax': rec.company_id.currency_id.round(sub_amount_tax),
				'sub_amount_total': sub_amount_untaxed + sub_amount_tax,
			})


class AnalyticSaleOrderLine(models.TransientModel):
	_name = "wizard.invoice.batch.lines"

	@api.depends('product_id')
	def _compute_product_name(self):
		for rec in self:
			if rec.product_id.description:
				rec.name = rec.product_id.description
			else:
				rec.name = rec.product_id.name

	name = fields.Text(string='Descripción',
					   default=_compute_product_name, store=True)
	product_id = fields.Many2one(
		'product.product', string='Producto', required=True, domain=[('fixed_concept','=',True)])
	product_uom_qty = fields.Float(
		string='Cantidad', default=1.0, required=True)
	product_uom = fields.Many2one(
		'uom.uom', related='product_id.uom_id', string='Unidad de medida', required=True)

	price_unit = fields.Float('Precio unitario', default=0.0)
	tax_ids = fields.Many2many('account.tax', string='Impuestos', domain=[('active', '=', True), ('type_tax_use', '=', 'sale')])
	discount = fields.Float(string='Discount (%)', default=0.0)

	subscription_product_line_id = fields.Many2one(
		'wizard.invoice.batch',
		string="Contract Product Lines",
	)
	price_subtotal = fields.Float(
		compute='_compute_amount',
		string='Subtotal',
		readonly=True,
		store=True
	)
	price_tax = fields.Float(
		compute='_compute_amount',
		string='Impuestos',
		readonly=True,
		store=True
	)
	price_total = fields.Float(
		compute='_compute_amount',
		string='Total',
		readonly=True,
		store=True
	)
	currency_id = fields.Many2one(
		'res.currency',
		string="Moneda",
	)

	product_no_variant_attribute_value_ids = fields.Many2many(
		'product.template.attribute.value', string='Product attribute values that do not create variants')

	@api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_ids')
	def _compute_amount(self):
		"""
		Compute the amounts of the SO line.
		"""
		for line in self:
			price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
			taxes = line.tax_ids.compute_all(price, line.subscription_product_line_id.currency_id, line.product_uom_qty,
											 product=line.product_id, partner=None)
			line.update({
				'price_tax': taxes['total_included'] - taxes['total_excluded'],
				'price_total': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
			})

	def _get_display_price(self, product):
		# TO DO: move me in master/saas-16 on sale.order
		# awa: don't know if it's still the case since we need the "product_no_variant_attribute_value_ids" field now
		# to be able to compute the full price

		# it is possible that a no_variant attribute is still in a variant if
		# the type of the attribute has been changed after creation.
		no_variant_attributes_price_extra = [
			ptav.price_extra for ptav in self.product_no_variant_attribute_value_ids.filtered(
				lambda ptav:
					ptav.price_extra and
					ptav not in product.product_template_attribute_value_ids
			)
		]
		if no_variant_attributes_price_extra:
			product = product.with_context(
				no_variant_attributes_price_extra=no_variant_attributes_price_extra
			)

		if self.subscription_product_line_id.pricelist_id.discount_policy == 'with_discount':
			return product.with_context(pricelist=self.subscription_product_line_id.pricelist_id.id).price
		product_context = dict(self.env.context, partner_id=self.subscription_product_line_id.partner_id.id,
							   date=self.subscription_product_line_id.date_order, uom=self.product_uom.id)

		final_price, rule_id = self.subscription_product_line_id.pricelist_id.with_context(product_context).get_product_price_rule(
			self.product_id, self.product_uom_qty or 1.0, self.subscription_product_line_id.partner_id)
		base_price, currency = self.with_context(product_context)._get_real_price_currency(
			product, rule_id, self.product_uom_qty, self.product_uom, self.subscription_product_line_id.pricelist_id.id)
		if currency != self.subscription_product_line_id.pricelist_id.currency_id:
			base_price = currency._convert(
				base_price, self.subscription_product_line_id.pricelist_id.currency_id,
				self.subscription_product_line_id.company_id or self.env.user.company_id, fields.Date.today())
		# negative discounts (= surcharge) are included in the display price
		return max(base_price, final_price)

	def _compute_tax_id(self):
		for line in self:
			#fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
			# If company_id is set, always filter taxes by the company
			taxes = line.product_id.taxes_id.filtered(lambda r: not line.subscription_product_line_id.company_id or r.company_id == line.subscription_product_line_id.company_id)
			line.tax_ids = taxes
			#line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id) if fpos else taxes

	@api.onchange('product_id')
	def product_id_change_p(self):
		if not self.product_id or not self.subscription_product_line_id.pricelist_id:
			return {'domain': {'product_uom': []}}
		vals = {}
		domain = {'product_uom': [
			('category_id', '=', self.product_id.uom_id.category_id.id)]}
		if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
			vals['product_uom'] = self.product_id.uom_id
			vals['product_uom_qty'] = self.product_uom_qty or 1.0

		print("llamare a product_id with_Context")
		product = self.product_id.with_context(
			lang=None,
			partner=None,
			quantity=vals.get('product_uom_qty') or self.product_uom_qty,
			date=fields.date.today(),
			pricelist=self.subscription_product_line_id.pricelist_id.id,
			uom=self.product_uom.id
		)

		result = {'domain': domain}

		name = self.product_id.name  # (product)

		vals.update(name=name)

		#self._compute_tax_id()
		self.tax_ids = product.taxes_id
		if self.subscription_product_line_id.pricelist_id:
			vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(
				product), product.taxes_id, self.tax_ids, self.subscription_product_line_id.company_id)
		self.update(vals)

		title = False
		message = False
		warning = {}
		"""if product.sale_line_warn != 'no-message':
			title = _("Warning for %s") % product.namesale_line_warn
			message = product.sale_line_warn_msg
			warning['title'] = title
			warning['message'] = message
			result = {'warning': warning}
			if product.sale_line_warn == 'block':
				self.product_id = False"""

		return result
	
	@api.onchange('price_unit')
	def _onchange_price_unit(self):
		if self.price_unit:
			price_text = str(self.price_unit)
			splitter = price_text.split(".")
			if len(splitter) == 2:
				qty_entire = len(splitter[0])
				#la decimal siempre se asumira como 2 digitos
				if qty_entire > 9:
					raise UserError("La cantidad de digitos en precio no puede ser mayor a 11 incluida la parte decimal")