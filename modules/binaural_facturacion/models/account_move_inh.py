from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from collections import defaultdict
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import ast
import json
import re
import warnings

import logging
_logger = logging.getLogger(__name__)


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

    @api.onchange("date_reception")
    def _onchange_date_reception(self):
        if self.is_invoice() and self.date_reception and self.invoice_date and self.date_reception < self.invoice_date:
            raise ValidationError("Fecha de recepcion no puede ser menor a fecha de factura")

    def _write(self, vals):
        res = super(AccountMoveBinauralFacturacion, self)._write(vals)
        if 'date_reception' in vals:
            self._compute_days_expired()
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
                _logger.info("Days expired %s",days_expired)
            i.days_expired = days_expired if days_expired > 0 else 0
        
    @api.depends('partner_id')
    def _get_vat(self):
        for p in self:
            if p.partner_id.prefix_vat and p.partner_id.vat:
                vat = str(p.partner_id.prefix_vat) + str(p.partner_id.vat)
            else:
                vat = str(p.partner_id.vat)
            p.vat = vat

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
            if move.is_sale_document(include_receipts=False):
                #incrementar numero de control de factura y Nota de credito de manera automatica
                sequence = move.sequence()
                next_correlative = sequence.get_next_char(sequence.number_next_actual) 
                correlative = sequence.next_by_id(sequence.id)
                move.write({'correlative':correlative})
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
                            raise ValidationError(_('La entrada registrada debe tener un número de secuencia único por empresa y Proveedor.\n'
                            'Números problemáticos: %s\n') % ', '.join(r[1] for r in res))

    @api.depends('journal_id', 'date')
    def _compute_highest_name(self):
        for record in self:
            #No aplicar para documentos de compras
            if not record.is_purchase_document(include_receipts=True):
                record.highest_name = record._get_last_sequence()
            else:
                record.highest_name = '/'
<<<<<<< HEAD
    
    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        #No aplicar para documentos de compras
        if not self.is_purchase_document(include_receipts=True):

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
            
    @api.constrains('invoice_line_ids')
    def qty_line_invocie(self):
        for record in self:
            if record.move_type in ['out_invoice', 'out_refund']:
                raise ValidationError("1")
                qty_max = int(self.env['ir.config_parameter'].sudo().get_param('qty_max'))
                if qty_max and qty_max < len(record.invoice_line_ids):
                    raise ValidationError("La cantidad de lineas de la factura es mayor a la cantidad configurada")
=======

    
>>>>>>> 6595a8a053ee3c095b79e4558031a7eddfac8e8f
