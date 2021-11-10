# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class AccountMoveCummingFacturacion(models.Model):
	_inherit = 'account.move'


	@api.constrains('amount_total','invoice_payment_term_id')
	def _onchange_limit_credit(self):
		for record in self:
			_logger.info("record.invoice_payment_term_id %s",record.invoice_payment_term_id)
			_logger.info("record.env.ref('account.account_payment_term_immediate') %s",record.env.ref('account.account_payment_term_immediate'))
			_logger.info("record.partner_id.credit_limit %s",record.partner_id.credit_limit)
			record.ensure_one()
			if record.state in ['draft', 'sent'] and record.partner_id.credit_limit > 0 and record.invoice_payment_term_id != record.env.ref('account.account_payment_term_immediate'):
				due = record.partner_id.total_due + record.amount_total
				if due > record.partner_id.credit_limit:
					raise UserError(_("El cliente no tiene un límite de crédito disponible"))
				

	def action_post(self):
		for record in self:
			due = record.partner_id.total_due + record.amount_total
			_logger.info("DUE %s",due)
			_logger.info("CREDIT LIMIT %s",record.partner_id.credit_limit)
			_logger.info("record.invoice_payment_term_id %s",record.invoice_payment_term_id)
			if due > record.partner_id.credit_limit and record.partner_id.credit_limit > 0 and record.invoice_payment_term_id != record.env.ref('account.account_payment_term_immediate'):
				raise UserError(_("El cliente no tiene un límite de crédito disponible"))
		res = super(AccountMoveCummingFacturacion, self).action_post()
		return res

	