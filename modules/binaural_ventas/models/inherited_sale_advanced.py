from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class SaleAdvancePaymentInvBinaural(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection([
        ('delivered', 'Regular invoice'),
        ('contingence', 'Factura de contingencia'),
        ('percentage', 'Down payment (percentage)'),
        ('fixed', 'Down payment (fixed amount)')
    ], string='Create Invoice', default='delivered', required=True,
        help="A standard invoice is issued with all the order lines ready for invoicing, \
            according to their invoicing policy (based on ordered or delivered quantity).")

    def create_invoices(self):
        _logger.info('Creando factura')
        sale_orders = self.env['sale.order'].browse(
            self._context.get('active_ids', []))
        _logger.info('Ordenes')
        _logger.info(sale_orders)
        qty_max = int(
            self.env['ir.config_parameter'].sudo().get_param('qty_max'))
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
            elif self.advance_payment_method == 'contingence':
                sale_orders._create_invoices(
                    final=self.deduct_down_payments, contingence=True)
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
                    tax_ids = order.fiscal_position_id.map_tax(
                        taxes, self.product_id, order.partner_shipping_id).ids
                    analytic_tag_ids = []
                    for line in order.order_line:
                        analytic_tag_ids = [(4, analytic_tag.id, None)
                                            for analytic_tag in line.analytic_tag_ids]

                    so_line_values = self._prepare_so_line(
                        order, analytic_tag_ids, tax_ids, amount)
                    so_line = sale_line_obj.create(so_line_values)
                    self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}
