# -*- coding: utf-8 -*-

from odoo import models, api, exceptions, fields


class AccountMoveAction(models.Model):
    _inherit = 'account.move'

    action_number = fields.Char(string='Número de Acción', readonly=True)

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        values = super(AccountMoveAction, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)
        if invoice.action_number:
            values.update({
                'action_number': invoice.action_number,
            })
        return values
    
    def check_solvent_partner(self):
        for record in self:
            invoices = record.partner_id.invoice_ids.filtered(lambda x: x.state in ['draft', 'open'])
            if len(invoices) > 0:
                record.partner_id.write({'is_solvent': False})
            else:
                record.partner_id.write({'is_solvent': True})

    def write(self, vals):
        res = super(AccountMoveAction, self).write(vals)
        self.check_solvent_partner()
        return res

    @api.model
    def create(self, vals):
        res = super(AccountMoveAction, self).create(vals)
        res.partner_id.write({'is_solvent': False})
        return res

    @api.onchange('partner_id')
    def _get_action_number(self):
        self.action_number = self.partner_id.action_number.number

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        val = super(AccountMoveAction, self)._prepare_refund(invoice=invoice, date_invoice=date_invoice, date=date,
                                                           description=description, journal_id=journal_id)
        invoice_id = self.env.context.get('active_id', False)
        val.update({'action_number': invoice.action_number})
        return val
    
    
class AccountMoveLineAction(models.Model):
    _inherit = 'account.move.line'

    action_number = fields.Char(related='partner_id.action_number.number', string='Número de Acción')