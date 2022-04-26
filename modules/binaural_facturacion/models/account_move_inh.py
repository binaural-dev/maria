import logging
from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools import float_compare
from odoo.tools.misc import formatLang, format_date, get_lang

_logger = logging.getLogger(__name__)
from .. models import funtions_retention


class AccountMoveBinauralFacturacion(models.Model):
	_inherit = 'account.move'

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

	def default_alternate_currency(self):
		alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))

		if alternate_currency:
			return alternate_currency
		else:
			return False

	@api.depends('invoice_line_ids.price_total', 'foreign_currency_rate')
	def _amount_all_foreign(self):
		"""
		Compute the foreign total amounts of the SO.
		"""
		for order in self:
			#se cambio de sumar en $ y luego multiplicar a sumar el subtotal en bs directamente
			foreign_amount_untaxed = foreign_amount_tax = 0.0
			for line in order.invoice_line_ids:
				#foreign_amount_untaxed += line.price_subtotal
				foreign_amount_untaxed +=line.foreign_subtotal
			foreign_amount_tax += order.amount_tax
			#foreign_amount_untaxed *= order.foreign_currency_rate
			foreign_amount_tax *= order.foreign_currency_rate
			foreign_amount_residual = order.amount_residual * order.foreign_currency_rate
			order.update({
				'foreign_amount_untaxed': foreign_amount_untaxed,
				'foreign_amount_tax': foreign_amount_tax,
				'foreign_amount_total': foreign_amount_untaxed + foreign_amount_tax,
				'foreign_amount_residual': foreign_amount_residual,
			})


	def default_currency_rate(self):
		rate = 0
		alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
		if alternate_currency:
			currency = self.env['res.currency.rate'].search([('currency_id', '=', alternate_currency)], limit=1,
															order='name desc')
			rate = currency.rate

		return rate
	@api.model_create_multi
	def create(self, vals_list):
		#chismoso de tasa parte 1
		flag = False
		rate = 0
		for record in vals_list:
			rate = record.get('foreign_currency_rate', False)
			if rate:
				rate = round(rate, 2)
				alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
				if alternate_currency:
					currency = self.env['res.currency.rate'].search([('currency_id', '=', alternate_currency)], limit=1,
																	order='name desc')
					if rate != currency.rate:
						flag = True
		#fin de chismoso de tasa parte 1

		obj_retention_islr = False
		if 'retention_islr_line_ids' in vals_list:
			obj_retention_islr = vals_list['retention_islr_line_ids']
		res = super(AccountMoveBinauralFacturacion, self).create(vals_list)

		if obj_retention_islr:
			vals_list['retention_islr_line_ids'] = obj_retention_islr

		if 'retention_islr_line_ids' in vals_list:
			_logger.info('Paso aqui')
			for line in vals_list['retention_islr_line_ids']:
				_logger.info('Paso aqui2')
				line[2]['invoice_id'] = res['id']
			self.env['account.retention'].create({
				'type': 'in_invoice',
				'type_retention': 'islr',
				'partner_id': vals_list['partner_id'],
				'retention_line': vals_list['retention_islr_line_ids'],
				'date_accounting': vals_list['date'],
				'date': vals_list['date'],
			})

		if flag:
			old_rate = self.default_currency_rate()
			# El usuario xxxx ha usado una tasa personalizada, la tasa del sistema para la fecha del pago xxx es de xxxx y ha usada la tasa personalizada xxx
			display_msg = "El usuario " + self.env.user.name + " ha usado una tasa personalizada,"
			display_msg += " la tasa del sistema para la fecha " + str(fields.Date.today()) + " es de "
			display_msg += str(old_rate) + " y ha usada la tasa personalizada " + str(rate)
			res.message_post(body=display_msg)
		_logger.info('resssssssssssssssssssssssssssssssssssssssss')
		_logger.info(res)


		return res
	
	def _check_origin_invoice(self):
		sale = self.env['account.journal'].search([('name', '=', self.invoice_orgin)], limit=1)
		if sale:
			return {'readonly': {
				'partner_id': True}}
		else:
			return
		
	correlative = fields.Char(string='Número de control',copy=False)
	is_contingence = fields.Boolean(string='Es contingencia',default=False)

	phone = fields.Char(string='Teléfono', related='partner_id.phone')
	vat = fields.Char(string='RIF', compute='_get_vat')
	address = fields.Char(string='Dirección', related='partner_id.street')
	business_name = fields.Char(string='Razón Social', related='partner_id.business_name')

	date_reception = fields.Date(string='Fecha de recepción',copy=False)

	days_expired = fields.Integer('Dias vencidos en base a Fecha de recepción', compute='_compute_days_expired',copy=False)
	filter_partner = fields.Selection([('customer', 'Clientes'), ('supplier', 'Proveedores'), ('contact', 'Contactos')],
									  string='Filtro de Contacto')

	amount_by_group_base = fields.Binary(string="Tax amount by group",compute='_compute_invoice_taxes_by_group',help='Edit Tax amounts if you encounter rounding issues.')

	apply_retention_iva = fields.Boolean(string="¿Se aplico retención de iva?", default=False, copy=False)
	apply_retention_islr = fields.Boolean(string="¿Se aplico retención de islr?", default=False, copy=False)
	iva_voucher_number = fields.Char(string="Comprobante de Retención de IVA", readonly=False, copy=False)
	islr_voucher_number = fields.Char(string="Comprobante de Retención de ISLR", readonly=False, copy=False)
	# Foreing cyrrency fields
	foreign_currency_id = fields.Many2one('res.currency', default=default_alternate_currency,
										  tracking=True)
	foreign_currency_rate = fields.Float(string="Tasa", tracking=True)
	foreign_currency_date = fields.Date(string="Fecha", default=fields.Date.today(), tracking=True)

	foreign_amount_untaxed = fields.Monetary(string='Base Imponible', store=True, readonly=True,
											 compute='_amount_all_foreign',
											 tracking=5)
	foreign_amount_tax = fields.Monetary(string='Impuestos', store=True, readonly=True, compute='_amount_all_foreign')
	foreign_amount_total = fields.Monetary(string='Total moneda alterna', store=True, readonly=True, compute='_amount_all_foreign',
										   tracking=4)
	foreign_amount_by_group = fields.Binary(string="Monto de impuesto por grupo",
											compute='_compute_invoice_taxes_by_group')
	foreign_amount_by_group_base = fields.Binary(string="Monto de impuesto por grupo",
												 compute='_compute_invoice_taxes_by_group')

	foreign_amount_residual = fields.Binary(string="Importe adeudado alterno",
												 compute='_amount_all_foreign')
	
	retention_iva_line_ids = fields.One2many('account.retention.line', 'invoice_id', domain=[('retention_id.type_retention', '=', 'iva')])
	generate_retencion_iva = fields.Boolean(string="Generar Retención IVA", default=False, copy=False)

	retention_islr_line_ids = fields.One2many('account.retention.line', 'invoice_id', domain=[('retention_id.type_retention', '=', 'islr')])

	@api.constrains('foreign_currency_rate')
	def _check_foreign_currency_rate(self):
		for record in self:
			if record.foreign_currency_rate <= 0:
				raise UserError("La tasa de la factura debe ser mayor que cero ")

	@api.depends('company_id', 'invoice_filter_type_domain', 'is_contingence')
	def _compute_suitable_journal_ids(self):
		for m in self:
			journal_type = m.invoice_filter_type_domain or 'general'
			company_id = m.company_id.id or self.env.company.id
			domain = [('company_id', '=', company_id), ('type', '=', journal_type),
					  ('journal_contingence', '=', m.is_contingence)]
			m.suitable_journal_ids = self.env['account.journal'].search(domain)

	@api.model
	def _search_default_journal(self, journal_types):
		is_contingence = self._context.get('default_is_contingence')
		company_id = self._context.get('default_company_id', self.env.company.id)
		if is_contingence:
			domain = [('company_id', '=', company_id), ('type', 'in', journal_types),
					  ('journal_contingence', '=', is_contingence)]
		else:
			domain = [('company_id', '=', company_id), ('type', 'in', journal_types)]
		
		journal = None
		if self._context.get('default_currency_id'):
			currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
			journal = self.env['account.journal'].search(currency_domain, limit=1)
			_logger.info('Diario por moneda')
		if not journal:
			journal = self.env['account.journal'].search(domain, limit=1)
		if not journal:
			company = self.env['res.company'].browse(company_id)
			
			error_msg = _(
				"No journal could be found in company %(company_name)s for any of those types: %(journal_types)s",
				company_name=company.display_name,
				journal_types=', '.join(journal_types),
			)
			raise UserError(error_msg)
		
		return journal

	@api.model
	def _get_default_journal(self):
		''' Get the default journal.
		It could either be passed through the context using the 'default_journal_id' key containing its id,
		either be determined by the default type.
		'''
		move_type = self._context.get('default_move_type', 'entry')
		if move_type in self.get_sale_types(include_receipts=True):
			journal_types = ['sale']
		elif move_type in self.get_purchase_types(include_receipts=True):
			journal_types = ['purchase']
		else:
			journal_types = self._context.get('default_move_journal_types', ['general'])
		
		if self._context.get('default_journal_id'):
			journal = self.env['account.journal'].browse(self._context['default_journal_id'])
			
			if move_type != 'entry' and journal.type not in journal_types:
				raise UserError(_(
					"Cannot create an invoice of type %(move_type)s with a journal having %(journal_type)s as type.",
					move_type=move_type,
					journal_type=journal.type,
				))
		else:
			journal = self._search_default_journal(journal_types)
		if self.is_contingence and not journal.journal_contingence:
			journal_new = self.env['account.journal'].browse([('journal_contingence', '=', True)], limit=1)
			if journal_new:
				journal = journal_new
		return journal

	@api.depends('line_ids.price_subtotal', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id', 'currency_id')
	def _compute_invoice_taxes_by_group(self):
		''' Helper to get the taxes grouped according their account.tax.group.
		This method is only used when printing the invoice.
		'''
		for move in self:
			lang_env = move.with_context(lang=move.partner_id.lang).env
			tax_lines = move.line_ids.filtered(lambda line: line.tax_line_id)
			tax_balance_multiplicator = -1 if move.is_inbound(True) else 1
			res = {}
			# There are as many tax line as there are repartition lines
			done_taxes = set()
			for line in tax_lines:
				res.setdefault(line.tax_line_id.tax_group_id, {'base': 0.0, 'amount': 0.0})
				res[line.tax_line_id.tax_group_id]['amount'] += tax_balance_multiplicator * (line.amount_currency if line.currency_id else line.balance)
				tax_key_add_base = tuple(move._get_tax_key_for_group_add_base(line))
				if tax_key_add_base not in done_taxes:
					if line.currency_id and line.company_currency_id and line.currency_id != line.company_currency_id:
						amount = line.company_currency_id._convert(line.tax_base_amount, line.currency_id, line.company_id, line.date or fields.Date.context_today(self))
					else:
						amount = line.tax_base_amount
					res[line.tax_line_id.tax_group_id]['base'] += amount
					# The base should be added ONCE
					done_taxes.add(tax_key_add_base)

			# At this point we only want to keep the taxes with a zero amount since they do not
			# generate a tax line.
			zero_taxes = set()
			for line in move.line_ids:
				for tax in line.tax_ids.flatten_taxes_hierarchy():
					if tax.tax_group_id not in res or tax.tax_group_id in zero_taxes:
						res.setdefault(tax.tax_group_id, {'base': 0.0, 'amount': 0.0})
						res[tax.tax_group_id]['base'] += tax_balance_multiplicator * (line.amount_currency if line.currency_id else line.balance)
						zero_taxes.add(tax.tax_group_id)

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

			move.foreign_amount_by_group = [(
				group.name, amounts['amount'] * move.foreign_currency_rate,
				amounts['base'] * move.foreign_currency_rate,
				formatLang(lang_env, amounts['amount'] * move.foreign_currency_rate,
						   currency_obj=move.foreign_currency_id),
				formatLang(lang_env, amounts['base'] * move.foreign_currency_rate,
						   currency_obj=move.foreign_currency_id),
				len(res),
				group.id
			) for group, amounts in res]

			move.foreign_amount_by_group_base = [(
				group.name.replace("IVA", "Total G").replace("TAX", "Total G"),
				amounts['base'] * move.foreign_currency_rate,
				amounts['amount'] * move.foreign_currency_rate,
				formatLang(lang_env, amounts['base'] * move.foreign_currency_rate,
						   currency_obj=move.foreign_currency_id),
				formatLang(lang_env, amounts['amount'] * move.foreign_currency_rate,
						   currency_obj=move.foreign_currency_id),
				len(res),
				group.id
			) for group, amounts in res]

	@api.onchange("date_reception")
	def _onchange_date_reception(self):
		if self.is_invoice() and self.date_reception and self.invoice_date and self.date_reception < self.invoice_date:
			raise ValidationError("Fecha de recepcion no puede ser menor a fecha de factura")

	def _write(self, vals):
		res = super(AccountMoveBinauralFacturacion, self)._write(vals)
		if 'date_reception' in vals:
			self._compute_days_expired()
		_logger.info('EDITAR FACTURAS')
		_logger.info(vals)
		_logger.info('EDITAR FACTURAS')
		return res

	@api.depends('date_reception', 'invoice_date_due', 'invoice_payment_term_id', 'state')
	def _compute_days_expired(self):
		days_expired = 0
		for i in self:
			if i.is_invoice() and i.state not in ['cancel'] and i.invoice_date_due and i.date_reception and i.invoice_date:
				if i.date_reception < i.invoice_date:
					raise ValidationError("No puedes asignar una fecha de recepción menor a la fecha de factura")
				diff = i.invoice_date_due - i.invoice_date
				date_today = fields.Date.today()
				try:
					real_due = i.date_reception+timedelta(days=diff.days)
					#payment_state: reversed invoicing_legacy
					if i.payment_state in ['not_paid','partial']:
						days_expired = (date_today - real_due).days
					elif i.payment_state in ['paid','in_payment']:
						lines = i._get_reconciled_invoices_partials()
						last_date = max(dt[2].date for dt in lines)
						_logger.info("la ultima fecha de conciliacion es %s",last_date)
						if last_date:
							days_expired = (last_date - real_due).days
				except Exception as e:
					_logger.info("Exepction en days expired")
					_logger.info(e)
					days_expired = 0
				_logger.info("Daysssss expired %s",days_expired)
			i.days_expired = days_expired if days_expired > 0 else 0

	@api.depends('partner_id')
	def _get_vat(self):
		for p in self:
			if p.partner_id.prefix_vat and p.partner_id.vat:
				vat = str(p.partner_id.prefix_vat) + str(p.partner_id.vat)
			else:
				vat = str(p.partner_id.vat)
			p.vat = vat.upper()

	def sequence(self):
		sequence = self.env['ir.sequence'].search([('code','=','invoice.correlative')])
		if not sequence:
			sequence = self.env['ir.sequence'].create({
				'name': 'Numero de correlativo de Factura',
				'code': 'invoice.correlative',
				'padding': 5
			})
		return sequence

	def _post(self, soft=True):
		"""Post/Validate the documents.

		Posting the documents will give it a number, and check that the document is
		complete (some fields might not be required if not posted but are required
		otherwise).
		If the journal is locked with a hash table, it will be impossible to change
		some fields afterwards.

		:param soft (bool): if True, future documents are not immediately posted,
			but are set to be auto posted automatically at the set accounting date.
			Nothing will be performed on those documents before the accounting date.
		:return Model<account.move>: the documents that have been posted
		"""
		if soft:
			future_moves = self.filtered(lambda move: move.date > fields.Date.context_today(self))
			future_moves.auto_post = True
			for move in future_moves:
				msg = _('This move will be posted at the accounting date: %(date)s', date=format_date(self.env, move.date))
				move.message_post(body=msg)
			to_post = self - future_moves
		else:
			to_post = self

		# `user_has_group` won't be bypassed by `sudo()` since it doesn't change the user anymore.
		if not self.env.su and not self.env.user.has_group('account.group_account_invoice'):
			raise AccessError(_("You don't have the access rights to post an invoice."))
		for move in to_post:
			if not move.line_ids.filtered(lambda line: not line.display_type):
				raise UserError(_('You need to add a line before posting.'))
			if move.auto_post and move.date > fields.Date.context_today(self):
				date_msg = move.date.strftime(get_lang(self.env).date_format)
				raise UserError(_("This move is configured to be auto-posted on %s", date_msg))

			if not move.partner_id:
				if move.is_sale_document():
					raise UserError(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
				elif move.is_purchase_document():
					raise UserError(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

			if move.is_invoice(include_receipts=True) and float_compare(move.amount_total, 0.0, precision_rounding=move.currency_id.rounding) < 0:
				raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead. Use the action menu to transform it into a credit note or refund."))

			# Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
			# lines are recomputed accordingly.
			# /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
			# environment.
			if not move.invoice_date and move.is_invoice(include_receipts=True):
				move.invoice_date = fields.Date.context_today(self)
				move.with_context(check_move_validity=False)._onchange_invoice_date()

			# When the accounting date is prior to the tax lock date, move it automatically to the next available date.
			# /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
			# environment.
			if (move.company_id.tax_lock_date and move.date <= move.company_id.tax_lock_date) and (move.line_ids.tax_ids or move.line_ids.tax_tag_ids):
				move.date = move.company_id.tax_lock_date + timedelta(days=1)
				move.with_context(check_move_validity=False)._onchange_currency()

		# Create the analytic lines in batch is faster as it leads to less cache invalidation.
		to_post.mapped('line_ids').create_analytic_lines()
		to_post.write({
			'state': 'posted',
			'posted_before': True,
		})

		for move in to_post:
			move.message_subscribe([p.id for p in [move.partner_id] if p not in move.sudo().message_partner_ids])

			# Compute 'ref' for 'out_invoice'.
			if move._auto_compute_invoice_reference():
				to_write = {
					'payment_reference': move._get_invoice_computed_reference(),
					'line_ids': []
				}
				for line in move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
					to_write['line_ids'].append((1, line.id, {'name': to_write['payment_reference']}))
				move.write(to_write)

		for move in to_post:
			if move.is_sale_document() \
					and move.journal_id.sale_activity_type_id \
					and (move.journal_id.sale_activity_user_id or move.invoice_user_id).id not in (self.env.ref('base.user_root').id, False):
				move.activity_schedule(
					date_deadline=min((date for date in move.line_ids.mapped('date_maturity') if date), default=move.date),
					activity_type_id=move.journal_id.sale_activity_type_id.id,
					summary=move.journal_id.sale_activity_note,
					user_id=move.journal_id.sale_activity_user_id.id or move.invoice_user_id.id,
				)

		customer_count, supplier_count = defaultdict(int), defaultdict(int)
		for move in to_post:
			if move.is_sale_document():
				customer_count[move.partner_id] += 1
			elif move.is_purchase_document():
				supplier_count[move.partner_id] += 1
		for partner, count in customer_count.items():
			(partner | partner.commercial_partner_id)._increase_rank('customer_rank', count)
		for partner, count in supplier_count.items():
			(partner | partner.commercial_partner_id)._increase_rank('supplier_rank', count)

		# Trigger action for paid invoices in amount is zero
		to_post.filtered(
			lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
		).action_invoice_paid()

		# Force balance check since nothing prevents another module to create an incorrect entry.
		# This is performed at the very end to avoid flushing fields before the whole processing.
		to_post._check_balanced()

		#Binaural facturacion init code

		for move in to_post:
			#cliente
			if move.is_sale_document(include_receipts=False) and not move.correlative:
				#incrementar numero de control de factura y Nota de credito de manera automatica
				if move.journal_id and move.journal_id.fiscal:
					sequence = move.sequence()
					next_correlative = sequence.get_next_char(sequence.number_next_actual)
					correlative = sequence.next_by_id(sequence.id)
					move.write({'correlative':correlative})
			if move.generate_retencion_iva and not move.iva_voucher_number:
				retention = self.env['account.retention'].create({
					'type': 'in_invoice',
					'partner_id': move.partner_id.id,
					'type_retention': 'iva',
					'date_accounting': move.date,
					'date': move.date,
				})
				data = funtions_retention.load_line_retention(retention, [], move.id)
				retention.write({'retention_line': data})
				retention.action_emitted()
				move.write({'iva_voucher_number': retention.number, 'apply_retention_iva': True})
			if move.retention_islr_line_ids and not move.islr_voucher_number:
				for rislr in move.retention_islr_line_ids:
					if rislr.retention_id.type_retention in ['islr']:
						rislr.retention_id.write({'date': move.date, 'date_accounting': move.date})
						rislr.retention_id.action_emitted()
						move.write({'islr_voucher_number': rislr.retention_id.number, 'apply_retention_islr': True})
		return to_post

	#heredar constrain para permitir name duplicado solo en proveedor
	@api.constrains('name', 'journal_id', 'state')
	def _check_unique_sequence_number(self):

		moves = self.filtered(lambda move: move.state == 'posted')
		if not moves:
			return

		self.flush(['name', 'journal_id', 'move_type', 'state'])

		# /!\ Computed stored fields are not yet inside the database.
		self._cr.execute('''
			SELECT move2.id, move2.name
			FROM account_move move
			INNER JOIN account_move move2 ON
				move2.name = move.name
				AND move2.journal_id = move.journal_id
				AND move2.move_type = move.move_type
				AND move2.id != move.id
			WHERE move.id IN %s AND move2.state = 'posted'
		''', [tuple(moves.ids)])
		res = self._cr.fetchall()
		if res:
			for i in moves:
				if not i.is_invoice(include_receipts=True) or not i.is_purchase_document(include_receipts=True) :
					raise ValidationError(_('Posted journal entry must have an unique sequence number per company.\n'
					'Problematic numbers: %s\n') % ', '.join(r[1] for r in res))
				else:
					#verificar si es duplicado por el mismo proveedor
					for r in res:
						_logger.info("id a buscar %s",r[0])
						invoice = self.env['account.move'].sudo().browse(int(r[0]))
						if invoice.partner_id == i.partner_id and i.is_purchase_document(include_receipts=True):
							raise ValidationError(_('La factura Nro %s esta repetida para el proveedor %s.\n') %(', '.join(r[1] for r in res),i.partner_id.name))

	@api.depends('journal_id', 'date')
	def _compute_highest_name(self):
		for record in self:
			#No aplicar para documentos de compras
			if not record.is_purchase_document(include_receipts=True):
				record.highest_name = record._get_last_sequence()
			else:
				record.highest_name = '/'

	@api.depends('posted_before', 'state', 'journal_id', 'date')
	def _compute_name(self):
		#No aplicar para documentos de compras
		for record in self:
			if not record.is_purchase_document(include_receipts=True):
				def journal_key(move):
					return (move.journal_id, move.journal_id.refund_sequence and move.move_type)

				def date_key(move):
					return (move.date.year, move.date.month)

				grouped = defaultdict(  # key: journal_id, move_type
					lambda: defaultdict(  # key: first adjacent (date.year, date.month)
						lambda: {
							'records': self.env['account.move'],
							'format': False,
							'format_values': False,
							'reset': False
						}
					)
				)
				self = self.sorted(lambda m: (m.date, m.ref or '', m.id))
				highest_name = self[0]._get_last_sequence() if self else False

				# Group the moves by journal and month
				for move in self:
					if not highest_name and move == self[0] and not move.posted_before:
						# In the form view, we need to compute a default sequence so that the user can edit
						# it. We only check the first move as an approximation (enough for new in form view)
						pass
					elif (move.name and move.name != '/') or move.state != 'posted':
						try:
							if not move.posted_before:
								move._constrains_date_sequence()
							# Has already a name or is not posted, we don't add to a batch
							continue
						except ValidationError:
							# Has never been posted and the name doesn't match the date: recompute it
							pass
					group = grouped[journal_key(move)][date_key(move)]
					if not group['records']:
						# Compute all the values needed to sequence this whole group
						move._set_next_sequence()
						group['format'], group['format_values'] = move._get_sequence_format_param(move.name)
						group['reset'] = move._deduce_sequence_number_reset(move.name)
					group['records'] += move

				# Fusion the groups depending on the sequence reset and the format used because `seq` is
				# the same counter for multiple groups that might be spread in multiple months.
				final_batches = []
				for journal_group in grouped.values():
					for date_group in journal_group.values():
						if (
							not final_batches
							or final_batches[-1]['format'] != date_group['format']
							or final_batches[-1]['format_values'] != date_group['format_values']
						):
							final_batches += [date_group]
						elif date_group['reset'] == 'never':
							final_batches[-1]['records'] += date_group['records']
						elif (
							date_group['reset'] == 'year'
							and final_batches[-1]['records'][0].date.year == date_group['records'][0].date.year
						):
							final_batches[-1]['records'] += date_group['records']
						else:
							final_batches += [date_group]

				# Give the name based on previously computed values
				for batch in final_batches:
					for move in batch['records']:
						move.name = batch['format'].format(**batch['format_values'])
						batch['format_values']['seq'] += 1
					batch['records']._compute_split_sequence()
				self.filtered(lambda m: not m.name).name = '/'
			else:
				self.filtered(lambda m: not m.name).name = '/'

	@api.constrains('move_type', 'invoice_date', 'invoice_line_ids')
	def _check_qty_lines(self):
		for record in self:
			_logger.info('RECORD')
			_logger.info(record)
			#if not record.invoice_date:
			#    raise ValidationError("Debe ingresar fecha")
			if record.move_type in ['out_invoice', 'out_refund']:
				qty_max = int(self.env['ir.config_parameter'].sudo().get_param('qty_max'))
				if qty_max and qty_max < len(record.invoice_line_ids):
					#pass
					raise UserError("La cantidad de lineas de la factura "+str(len(record.invoice_line_ids))+" es mayor a la cantidad configurada "+str(qty_max))

	def action_register_payment(self):
		''' Open the account.payment.register wizard to pay the selected journal entries.
		:return: An action opening the account.payment.register wizard.
		'''
		res = super(AccountMoveBinauralFacturacion, self).action_register_payment()
		context = res.get('context')
		res['context'].setdefault('default_foreign_currency_rate', self[0].foreign_currency_rate)
		if self.foreign_currency_id:
			res['context'].setdefault('default_foreign_currency_id', self.foreign_currency_id.id)
		return res

	@api.onchange('foreign_currency_rate')
	def _onchange_rate(self):
		_logger.info("cambioooooooooooooooooooooooo")
		for a in self:
			if a.move_type == 'entry':
				for l in a.line_ids:
					l._onchange_amount_currency()

	def change_rate_async(self,rate):
		for m in self:
			m.foreign_currency_rate = rate

			#m._onchange_rate()
			m.line_ids.with_context(check_move_validity=False)._onchange_amount_currency_bin(rate)


class AcoountMoveLineBinauralFact(models.Model):
	_inherit = 'account.move.line'

	#Validar que no se permitan mas de dos tasas
	@api.onchange('tax_ids')
	def onchange_list_taxes(self):
		for line in self:
			_logger.warning([tax for tax in line.mapped('tax_ids')])
			if len([tax for tax in line.mapped('tax_ids')]) > 1:
				raise UserError("No puede agregar dos impuestos a la misma linea de factura")

	#validar que el precio unitario no sea mayor al costo del producto, basado en la configuracion
	@api.onchange('price_unit','product_id')
	def onchange_price_unit_check_cost(self):
		for l in self:
			if self.env['ir.config_parameter'].sudo().get_param('not_cost_higher_price_invoice') and l.price_unit and l.product_id:
				_logger.info("costo del producto %s",l.product_id.standard_price)
				_logger.info("precio unitario %s",l.price_unit)
				if l.price_unit <= l.product_id.standard_price and l.product_id.type == 'product' and l.move_id.is_sale_document(include_receipts=True):#solo aplica a almacenables
					raise ValidationError("Precio unitario no puede ser menor o igual al costo del producto")

	def default_alternate_currency(self):
		alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))

		if alternate_currency:
			return alternate_currency
		else:
			return False


	@api.depends('move_id.foreign_currency_rate','price_unit','quantity', 'tax_ids')
	def _amount_all_foreign(self):
		"""
		Compute the foreign total amounts of the SO.
		"""
		#duda el precio subtotal no deberia ser mejor precio unitario en bs por la cantidad? o se deja asi el subtotal en bs por la tasa
		for order in self:
			order.update({
				'foreign_price_unit': order.price_unit * order.move_id.foreign_currency_rate,
				'foreign_subtotal': order.price_subtotal * order.move_id.foreign_currency_rate,
			})

	foreign_price_unit = fields.Monetary(string='Precio Alterno', store=True, readonly=True,
										 compute='_amount_all_foreign', tracking=4)
	foreign_subtotal = fields.Monetary(string='Subtotal Alterno', store=True, readonly=True,
									   compute='_amount_all_foreign', tracking=4)
	foreign_currency_id = fields.Many2one('res.currency', default=default_alternate_currency, tracking=True)

	#foreign_currency_rate = fields.Float(string="Tasa", related='move_id.foreign_currency_rate', tracking=True)
	foreign_currency_rate = fields.Float(string="Tasa", related='move_id.foreign_currency_rate', digits=(16, 2),
										tracking=True, store=True)

	def reconcile(self):
		''' Reconcile the current move lines all together.
		:return: A dictionary representing a summary of what has been done during the reconciliation:
				* partials:             A recorset of all account.partial.reconcile created during the reconciliation.
				* full_reconcile:       An account.full.reconcile record created when there is nothing left to reconcile
										in the involved lines.
				* tax_cash_basis_moves: An account.move recordset representing the tax cash basis journal entries.
		'''
		results = {}

		if not self:
			return results

		# List unpaid invoices
		not_paid_invoices = self.move_id.filtered(
			lambda move: move.is_invoice(include_receipts=True) and move.payment_state not in ('paid', 'in_payment')
		)

		# ==== Check the lines can be reconciled together ====
		company = None
		account = None
		for line in self:
			if line.reconciled:
				raise UserError(_("You are trying to reconcile some entries that are already reconciled."))
			if not line.account_id.reconcile and line.account_id.internal_type != 'liquidity':
				raise UserError(_("Account %s does not allow reconciliation. First change the configuration of this account to allow it.")
								% line.account_id.display_name)
			if line.move_id.state != 'posted':
				raise UserError(_('You can only reconcile posted entries.'))
			if company is None:
				company = line.company_id
			elif line.company_id != company:
				raise UserError(_("Entries doesn't belong to the same company: %s != %s")
								% (company.display_name, line.company_id.display_name))
			if account is None:
				account = line.account_id
			elif line.account_id != account:
				raise UserError(_("Entries are not from the same account: %s != %s")
								% (account.display_name, line.account_id.display_name))

		sorted_lines = self.sorted(key=lambda line: (line.date_maturity or line.date, line.currency_id))

		# ==== Collect all involved lines through the existing reconciliation ====

		involved_lines = sorted_lines
		involved_partials = self.env['account.partial.reconcile']
		current_lines = involved_lines
		current_partials = involved_partials
		while current_lines:
			current_partials = (current_lines.matched_debit_ids + current_lines.matched_credit_ids) - current_partials
			involved_partials += current_partials
			current_lines = (current_partials.debit_move_id + current_partials.credit_move_id) - current_lines
			involved_lines += current_lines

		# ==== Create partials ====

		partials = self.env['account.partial.reconcile'].create(sorted_lines._prepare_reconciliation_partials())

		# Track newly created partials.
		results['partials'] = partials
		involved_partials += partials

		# ==== Create entries for cash basis taxes ====

		is_cash_basis_needed = account.user_type_id.type in ('receivable', 'payable')
		if is_cash_basis_needed and not self._context.get('move_reverse_cancel'):
			tax_cash_basis_moves = partials._create_tax_cash_basis_moves()
			results['tax_cash_basis_moves'] = tax_cash_basis_moves

		# ==== Check if a full reconcile is needed ====

		if involved_lines[0].currency_id and all(line.currency_id == involved_lines[0].currency_id for line in involved_lines):
			is_full_needed = all(line.currency_id.is_zero(line.amount_residual_currency) for line in involved_lines)
		else:
			is_full_needed = all(line.company_currency_id.is_zero(line.amount_residual) for line in involved_lines)

		if is_full_needed:

			# ==== Create the exchange difference move ====
			exchange_move = None
			"""if self._context.get('no_exchange_difference'):
				exchange_move = None
			else:
				exchange_move = involved_lines._create_exchange_difference_move()
				if exchange_move:
					exchange_move_lines = exchange_move.line_ids.filtered(lambda line: line.account_id == account)

					# Track newly created lines.
					involved_lines += exchange_move_lines

					# Track newly created partials.
					exchange_diff_partials = exchange_move_lines.matched_debit_ids \
											 + exchange_move_lines.matched_credit_ids
					involved_partials += exchange_diff_partials
					results['partials'] += exchange_diff_partials

					exchange_move._post(soft=False)

			# ==== Create the full reconcile ===="""

			results['full_reconcile'] = self.env['account.full.reconcile'].create({
				'exchange_move_id': exchange_move and exchange_move.id,
				'partial_reconcile_ids': [(6, 0, involved_partials.ids)],
				'reconciled_line_ids': [(6, 0, involved_lines.ids)],
			})

		# Trigger action for paid invoices
		not_paid_invoices\
			.filtered(lambda move: move.payment_state in ('paid', 'in_payment'))\
			.action_invoice_paid()

		return results

	#@api.onchange('amount_currency')
	def _onchange_amount_currency_bin(self,rate):
		_logger.info("TRIGGER ")
		for line in self:
			company = line.move_id.company_id
			balance = line.currency_id._convert(line.amount_currency, company.currency_id, company, line.move_id.date,True,rate)
			line.with_context(check_move_validity=False).debit = balance if balance > 0.0 else 0.0
			line.with_context(check_move_validity=False).credit = -balance if balance < 0.0 else 0.0

	@api.onchange('amount_currency')
	def _onchange_amount_currency(self):
		_logger.info("TRIGGER ORIGNAL")
		for line in self:
			company = line.move_id.company_id
			balance = line.currency_id._convert(line.amount_currency, company.currency_id, company, line.move_id.date,True,line.move_id.foreign_currency_rate)
			line.debit = balance if balance > 0.0 else 0.0
			line.credit = -balance if balance < 0.0 else 0.0

			if not line.move_id.is_invoice(include_receipts=True):
				continue

			line.update(line._get_fields_onchange_balance())
			line.update(line._get_price_total_and_subtotal())
