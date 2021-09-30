# -*- coding: utf-8 -*-
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests.common import Form
from odoo.tests import tagged
from odoo import fields
from odoo.exceptions import UserError

from unittest.mock import patch
from datetime import timedelta
import logging
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)

@tagged('post_install', '-at_install')
class TestAccountMoveOutInvoiceBinauralFacturacion(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.invoice = cls.init_invoice('out_invoice', products=cls.product_a+cls.product_b)

        cls.product_line_vals_1 = {
            'name': cls.product_a.name,
            'product_id': cls.product_a.id,
            'account_id': cls.product_a.property_account_income_id.id,
            'partner_id': cls.partner_a.id,
            'product_uom_id': cls.product_a.uom_id.id,
            'quantity': 1.0,
            'discount': 0.0,
            'price_unit': 1000.0,
            'price_subtotal': 1000.0,
            'price_total': 1150.0,
            'tax_ids': cls.product_a.taxes_id.ids,
            'tax_line_id': False,
            'currency_id': cls.company_data['currency'].id,
            'amount_currency': -1000.0,
            'debit': 0.0,
            'credit': 1000.0,
            'date_maturity': False,
            'tax_exigible': True,
        }
        cls.product_line_vals_2 = {
            'name': cls.product_b.name,
            'product_id': cls.product_b.id,
            'account_id': cls.product_b.property_account_income_id.id,
            'partner_id': cls.partner_a.id,
            'product_uom_id': cls.product_b.uom_id.id,
            'quantity': 1.0,
            'discount': 0.0,
            'price_unit': 200.0,
            'price_subtotal': 200.0,
            'price_total': 260.0,
            'tax_ids': cls.product_b.taxes_id.ids,
            'tax_line_id': False,
            'currency_id': cls.company_data['currency'].id,
            'amount_currency': -200.0,
            'debit': 0.0,
            'credit': 200.0,
            'date_maturity': False,
            'tax_exigible': True,
        }
        cls.tax_line_vals_1 = {
            'name': cls.tax_sale_a.name,
            'product_id': False,
            'account_id': cls.company_data['default_account_tax_sale'].id,
            'partner_id': cls.partner_a.id,
            'product_uom_id': False,
            'quantity': 1.0,
            'discount': 0.0,
            'price_unit': 180.0,
            'price_subtotal': 180.0,
            'price_total': 180.0,
            'tax_ids': [],
            'tax_line_id': cls.tax_sale_a.id,
            'currency_id': cls.company_data['currency'].id,
            'amount_currency': -180.0,
            'debit': 0.0,
            'credit': 180.0,
            'date_maturity': False,
            'tax_exigible': True,
        }
        cls.tax_line_vals_2 = {
            'name': cls.tax_sale_b.name,
            'product_id': False,
            'account_id': cls.company_data['default_account_tax_sale'].id,
            'partner_id': cls.partner_a.id,
            'product_uom_id': False,
            'quantity': 1.0,
            'discount': 0.0,
            'price_unit': 30.0,
            'price_subtotal': 30.0,
            'price_total': 30.0,
            'tax_ids': [],
            'tax_line_id': cls.tax_sale_b.id,
            'currency_id': cls.company_data['currency'].id,
            'amount_currency': -30.0,
            'debit': 0.0,
            'credit': 30.0,
            'date_maturity': False,
            'tax_exigible': True,
        }
        cls.term_line_vals_1 = {
            'name': '',
            'product_id': False,
            'account_id': cls.company_data['default_account_receivable'].id,
            'partner_id': cls.partner_a.id,
            'product_uom_id': False,
            'quantity': 1.0,
            'discount': 0.0,
            'price_unit': -1410.0,
            'price_subtotal': -1410.0,
            'price_total': -1410.0,
            'tax_ids': [],
            'tax_line_id': False,
            'currency_id': cls.company_data['currency'].id,
            'amount_currency': 1410.0,
            'debit': 1410.0,
            'credit': 0.0,
            'date_maturity': fields.Date.from_string('2019-01-01'),
            'tax_exigible': True,
        }
        cls.move_vals = {
            'partner_id': cls.partner_a.id,
            'currency_id': cls.company_data['currency'].id,
            'journal_id': cls.company_data['default_journal_sale'].id,
            'date': fields.Date.from_string('2019-01-01'),
            'fiscal_position_id': False,
            'payment_reference': '',
            'invoice_payment_term_id': cls.pay_terms_a.id,
            'amount_untaxed': 1200.0,
            'amount_tax': 210.0,
            'amount_total': 1410.0,
        }

        cls.custom_payment_method_in = cls.env['account.payment.method'].create({
            'name': 'custom_payment_method_in',
            'code': 'CUSTOMIN',
            'payment_type': 'inbound',
        })

    def setUp(self):
        super(TestAccountMoveOutInvoiceBinauralFacturacion, self).setUp()
        self.assertInvoiceValues(self.invoice, [
            self.product_line_vals_1,
            self.product_line_vals_2,
            self.tax_line_vals_1,
            self.tax_line_vals_2,
            self.term_line_vals_1,
        ], self.move_vals)

    def test_out_invoice_post_correlative(self):
        ''' Verificar nro control es asignado de manera automatica en factura de cliente '''
        # Create an invoice with rate 1/3.
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': fields.Date.from_string('2016-01-01'),
            'date': fields.Date.from_string('2015-01-01'),
            'currency_id': self.currency_data['currency'].id,
            'invoice_payment_term_id': self.pay_terms_a.id,
            'invoice_line_ids': [
                (0, None, {
                    'name': self.product_line_vals_1['name'],
                    'product_id': self.product_line_vals_1['product_id'],
                    'product_uom_id': self.product_line_vals_1['product_uom_id'],
                    'quantity': self.product_line_vals_1['quantity'],
                    'price_unit': self.product_line_vals_1['price_unit'],
                    'tax_ids': self.product_line_vals_1['tax_ids'],
                }),
                (0, None, {
                    'name': self.product_line_vals_2['name'],
                    'product_id': self.product_line_vals_2['product_id'],
                    'product_uom_id': self.product_line_vals_2['product_uom_id'],
                    'quantity': self.product_line_vals_2['quantity'],
                    'price_unit': self.product_line_vals_2['price_unit'],
                    'tax_ids': self.product_line_vals_2['tax_ids'],
                }),
            ],
        })

        # Add a manual edition of a tax line:
        # - The modification must be preserved in the business fields.
        # - The journal entry must be balanced before / after the post.
        move.write({
            'line_ids': [
                (1, move.line_ids.filtered(lambda line: line.tax_line_id.id == self.tax_line_vals_1['tax_line_id']).id, {
                    'amount_currency': -200.0,
                }),
                (1, move.line_ids.filtered(lambda line: line.date_maturity).id, {
                    'amount_currency': 1430.0,
                }),
            ],
        })

        # Set the tax lock date:
        # - The date must be set automatically at the date after the tax_lock_date.
        # - As the date changed, the currency rate has changed (1/3 => 1/2).
        move.company_id.tax_lock_date = fields.Date.from_string('2016-12-31')

        #verificar el numero siguiente es el que sera escrito en la fatura al confirmar (_post)
        sequence = move.sequence()
        #get next value but not increment
        next_correlative = sequence.get_next_char(sequence.number_next_actual)
        move.action_post()
        self.assertInvoiceValues(move, [
            {
                **self.product_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -1000.0,
                'debit': 0.0,
                'credit': 500.0,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -200.0,
                'debit': 0.0,
                'credit': 100.0,
            },
            {
                **self.tax_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'price_unit': 200.0,
                'price_subtotal': 200.0,
                'price_total': 200.0,
                'amount_currency': -200.0,
                'debit': 0.0,
                'credit': 100.0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -30.0,
                'debit': 0.0,
                'credit': 15.0,
            },
            {
                **self.term_line_vals_1,
                'name': move.name,
                'currency_id': self.currency_data['currency'].id,
                'price_unit': -1430.0,
                'price_subtotal': -1430.0,
                'price_total': -1430.0,
                'amount_currency': 1430.0,
                'debit': 715.0,
                'credit': 0.0,
                'date_maturity': fields.Date.from_string('2016-01-01'),
            },
        ], {
            **self.move_vals,
            'payment_reference': move.name,
            'currency_id': self.currency_data['currency'].id,
            'date': fields.Date.from_string('2017-01-01'),
            'amount_untaxed': 1200.0,
            'amount_tax': 230.0,
            'amount_total': 1430.0,
            'correlative':next_correlative,
            'name':move.name,
        })


        #convertir a borrador, al validar nuevamente no incrementar nro control
        move.button_draft()
        move.action_post()
        self.assertInvoiceValues(move, [
            {
                **self.product_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -1000.0,
                'debit': 0.0,
                'credit': 500.0,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -200.0,
                'debit': 0.0,
                'credit': 100.0,
            },
            {
                **self.tax_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'price_unit': 200.0,
                'price_subtotal': 200.0,
                'price_total': 200.0,
                'amount_currency': -200.0,
                'debit': 0.0,
                'credit': 100.0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -30.0,
                'debit': 0.0,
                'credit': 15.0,
            },
            {
                **self.term_line_vals_1,
                'name': move.name,
                'currency_id': self.currency_data['currency'].id,
                'price_unit': -1430.0,
                'price_subtotal': -1430.0,
                'price_total': -1430.0,
                'amount_currency': 1430.0,
                'debit': 715.0,
                'credit': 0.0,
                'date_maturity': fields.Date.from_string('2016-01-01'),
            },
        ], {
            **self.move_vals,
            'payment_reference': move.name,
            'currency_id': self.currency_data['currency'].id,
            'date': fields.Date.from_string('2017-01-01'),
            'amount_untaxed': 1200.0,
            'amount_tax': 230.0,
            'amount_total': 1430.0,
            'correlative':next_correlative,
            'name':move.name,
        })
        
    

    def test_out_invoice_create_name_auto(self):
        # Test creating an account_move with the least information.
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': fields.Date.from_string('2019-01-01'),
            'currency_id': self.currency_data['currency'].id,
            'invoice_payment_term_id': self.pay_terms_a.id,
            'invoice_line_ids': [
                (0, None, {
                    'product_id': self.product_a.id,
                    'product_uom_id': self.product_a.uom_id.id,
                    'quantity': 1.0,
                    'price_unit': 1000.0,
                    'tax_ids': [(6, 0, self.product_a.taxes_id.ids)],
                }),
                (0, None, {
                    'product_id': self.product_b.id,
                    'product_uom_id': self.product_b.uom_id.id,
                    'quantity': 1.0,
                    'price_unit': 200.0,
                    'tax_ids': [(6, 0, self.product_b.taxes_id.ids)],
                }),
            ]
        })
        self.assertInvoiceValues(move, [
            {
                **self.product_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -1000.0,
                'credit': 500.0,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -200.0,
                'credit': 100.0,
            },
            {
                **self.tax_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -180.0,
                'credit': 90.0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -30.0,
                'credit': 15.0,
            },
            {
                **self.term_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 1410.0,
                'debit': 705.0,
            },
        ], {
            **self.move_vals,
            'currency_id': self.currency_data['currency'].id,
        })
        move.action_post()


        
        move2 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': fields.Date.from_string('2019-01-01'),
            'currency_id': self.currency_data['currency'].id,
            'invoice_payment_term_id': self.pay_terms_a.id,
            'invoice_line_ids': [
                (0, None, {
                    'product_id': self.product_a.id,
                    'product_uom_id': self.product_a.uom_id.id,
                    'quantity': 1.0,
                    'price_unit': 1000.0,
                    'tax_ids': [(6, 0, self.product_a.taxes_id.ids)],
                }),
                (0, None, {
                    'product_id': self.product_b.id,
                    'product_uom_id': self.product_b.uom_id.id,
                    'quantity': 1.0,
                    'price_unit': 200.0,
                    'tax_ids': [(6, 0, self.product_b.taxes_id.ids)],
                }),
            ]
        })
        self.assertInvoiceValues(move2, [
            {
                **self.product_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -1000.0,
                'credit': 500.0,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -200.0,
                'credit': 100.0,
            },
            {
                **self.tax_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -180.0,
                'credit': 90.0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -30.0,
                'credit': 15.0,
            },
            {
                **self.term_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 1410.0,
                'debit': 705.0,
            },
        ], {
            **self.move_vals,
            'currency_id': self.currency_data['currency'].id,
        })
        move2.action_post()

    def test_out_invoice_onchange_date_reception(self):
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': fields.Date.from_string('2019-01-01'),
            'currency_id': self.currency_data['currency'].id,
            'invoice_payment_term_id': self.pay_terms_a.id,
            'invoice_line_ids': [
                (0, None, {
                    'product_id': self.product_a.id,
                    'product_uom_id': self.product_a.uom_id.id,
                    'quantity': 1.0,
                    'price_unit': 1000.0,
                    'tax_ids': [(6, 0, self.product_a.taxes_id.ids)],
                }),
                (0, None, {
                    'product_id': self.product_b.id,
                    'product_uom_id': self.product_b.uom_id.id,
                    'quantity': 1.0,
                    'price_unit': 200.0,
                    'tax_ids': [(6, 0, self.product_b.taxes_id.ids)],
                }),
            ]
        })

        self.assertInvoiceValues(move, [
            {
                **self.product_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -1000.0,
                'credit': 500.0,
            },
            {
                **self.product_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -200.0,
                'credit': 100.0,
            },
            {
                **self.tax_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -180.0,
                'credit': 90.0,
            },
            {
                **self.tax_line_vals_2,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -30.0,
                'credit': 15.0,
            },
            {
                **self.term_line_vals_1,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 1410.0,
                'debit': 705.0,
            },
        ], {
            **self.move_vals,
            'currency_id': self.currency_data['currency'].id,
        })
        move.action_post()
        move.invoice_date_due = fields.Date.from_string('2019-01-03')
        move_form = Form(move)
        move_form.date_reception = fields.Date.from_string('2019-01-05')
        _logger.info("Dias expirados----------------- %s",move_form.days_expired)
        self.assertEqual(move_form.days_expired,self.calc_days_expired(fields.Date.from_string('2019-01-05')), "Dias de vencimiento en base a fecha de recepcion no coincide.")
        
        with self.assertRaises(ValidationError):
            move_form.date_reception = fields.Date.from_string('2018-12-31')


        active_ids = move.id
        payments = self.env['account.payment.register'].with_context(active_model='account.move', active_ids=active_ids).create({
            'amount': 2000.0,
            'group_payment': True,
            'payment_difference_handling': 'open',
            'currency_id': self.currency_data['currency'].id,
            'payment_method_id': self.custom_payment_method_in.id,
        })._create_payments()

        self.assertRecordValues(payments, [{
            'payment_method_id': self.custom_payment_method_in.id,
        }])
        self.assertRecordValues(payments.line_ids.sorted('balance'), [
            # Receivable line:
            {
                'debit': 0.0,
                'credit': 1000.0,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': -2000.0,
                'reconciled': False,
            },
            # Liquidity line:
            {
                'debit': 1000.0,
                'credit': 0.0,
                'currency_id': self.currency_data['currency'].id,
                'amount_currency': 2000.0,
                'reconciled': False,
            },
        ])
        _logger.info("move move.payment_state::::: %s",move.payment_state)
        move_form = Form(move)
        move_form.date_reception = fields.Date.from_string('2019-01-06')

        self.assertEqual(move_form.days_expired,self.calc_days_expired(fields.Date.from_string('2019-01-06')), "Dias de vencimiento en base a fecha de recepcion no coincide en factura pagada.")



    def calc_days_expired(self,reception):
        days_expired = 0
        due = fields.Date.from_string('2019-01-03')
        invoice_date = fields.Date.from_string('2019-01-01')

        days = (due - invoice_date).days
        today = fields.Date.today()

        real_due = reception+timedelta(days=days)
        days_expired = (today - real_due).days
        return days_expired
