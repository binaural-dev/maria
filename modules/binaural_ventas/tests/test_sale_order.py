# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import UserError, AccessError
from odoo.tests import Form, tagged
from odoo.tools import float_compare

from .common import TestSaleCommon


@tagged('post_install', '-at_install')
class TestSaleOrderBinauralVentas(TestSaleCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        SaleOrder = cls.env['sale.order'].with_context(tracking_disable=True)

        # set up users
        cls.crm_team0 = cls.env['crm.team'].create({
            'name': 'crm team 0',
            'company_id': cls.company_data['company'].id
        })
        cls.crm_team1 = cls.env['crm.team'].create({
            'name': 'crm team 1',
            'company_id': cls.company_data['company'].id
        })
        cls.user_in_team = cls.env['res.users'].create({
            'email': 'team0user@example.com',
            'login': 'team0user',
            'name': 'User in Team 0',
            'sale_team_id': cls.crm_team0.id
        })
        cls.user_not_in_team = cls.env['res.users'].create({
            'email': 'noteamuser@example.com',
            'login': 'noteamuser',
            'name': 'User Not In Team',
        })

        # create a generic Sale Order with all classical products and empty pricelist
        cls.sale_order = SaleOrder.create({
            'partner_id': cls.partner_a.id,
            'partner_invoice_id': cls.partner_a.id,
            'partner_shipping_id': cls.partner_a.id,
            'pricelist_id': cls.company_data['default_pricelist'].id,
        })
        cls.sol_product_order = cls.env['sale.order.line'].create({
            'name': cls.company_data['product_order_no'].name,
            'product_id': cls.company_data['product_order_no'].id,
            'product_uom_qty': 2,
            'product_uom': cls.company_data['product_order_no'].uom_id.id,
            'price_unit': cls.company_data['product_order_no'].list_price,
            'order_id': cls.sale_order.id,
            'tax_id': False,
        })
        cls.sol_serv_deliver = cls.env['sale.order.line'].create({
            'name': cls.company_data['product_service_delivery'].name,
            'product_id': cls.company_data['product_service_delivery'].id,
            'product_uom_qty': 2,
            'product_uom': cls.company_data['product_service_delivery'].uom_id.id,
            'price_unit': cls.company_data['product_service_delivery'].list_price,
            'order_id': cls.sale_order.id,
            'tax_id': False,
        })
        cls.sol_serv_order = cls.env['sale.order.line'].create({
            'name': cls.company_data['product_service_order'].name,
            'product_id': cls.company_data['product_service_order'].id,
            'product_uom_qty': 2,
            'product_uom': cls.company_data['product_service_order'].uom_id.id,
            'price_unit': cls.company_data['product_service_order'].list_price,
            'order_id': cls.sale_order.id,
            'tax_id': False,
        })
        cls.sol_product_deliver = cls.env['sale.order.line'].create({
            'name': cls.company_data['product_delivery_no'].name,
            'product_id': cls.company_data['product_delivery_no'].id,
            'product_uom_qty': 2,
            'product_uom': cls.company_data['product_delivery_no'].uom_id.id,
            'price_unit': cls.company_data['product_delivery_no'].list_price,
            'order_id': cls.sale_order.id,
            'tax_id': False,
        })

    def test_sale_with_taxes(self):
        """ Test SO with taxes applied on its lines and check subtotal applied on its lines and total applied on the SO """
        # Create a tax with price included
        tax_include = self.env['account.tax'].create({
            'name': 'Tax with price include',
            'amount': 10,
            'price_include': True
        })
        # Create a tax with price not included
        tax_exclude = self.env['account.tax'].create({
            'name': 'Tax with no price include',
            'amount': 10,
        })

        # Apply taxes on the sale order lines
        self.sol_product_order.write({'tax_id': [(4, tax_include.id)]})
        self.sol_serv_deliver.write({'tax_id': [(4, tax_include.id)]})
        self.sol_serv_order.write({'tax_id': [(4, tax_exclude.id)]})
        self.sol_product_deliver.write({'tax_id': [(4, tax_exclude.id)]})

        # Trigger onchange to reset discount, unit price, subtotal, ...
        for line in self.sale_order.order_line:
            line.product_id_change()
            line._onchange_discount()

        for line in self.sale_order.order_line:
            if line.tax_id.price_include:
                price = line.price_unit * line.product_uom_qty - line.price_tax
            else:
                price = line.price_unit * line.product_uom_qty

            self.assertEqual(float_compare(line.price_subtotal, price, precision_digits=2), 0)

        self.assertEqual(self.sale_order.amount_total,
                          self.sale_order.amount_untaxed + self.sale_order.amount_tax,
                          'Taxes should be applied')

    