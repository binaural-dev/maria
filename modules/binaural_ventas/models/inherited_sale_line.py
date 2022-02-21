from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare
import logging
_logger = logging.getLogger(__name__)


class SaleOrderLineBinauralVentas(models.Model):
    _inherit = 'sale.order.line'

    def default_alternate_currency(self):
        alternate_currency = int(
            self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))

        if alternate_currency:
            return alternate_currency
        else:
            return False

    @api.depends('order_id.foreign_currency_rate', 'price_unit', 'product_uom_qty')
    def _amount_all_foreign(self):
        """
        Compute the foreign total amounts of the SO.
        """
        decimal_function = self.env['decimal.precision'].search(
            [('name', '=', 'decimal_quantity')])
        for order in self:
            name_foreign_currency = order.order_id.foreign_currency_id.name
            name_base_currency = 'USD' if name_foreign_currency == 'VEF' else 'VEF'
            value_rate = 0
            if name_foreign_currency:
                value_rate = decimal_function.getCurrencyValue(
                rate=order.order_id.foreign_currency_rate, base_currency=name_base_currency, foreign_currency=name_foreign_currency)

            order.update({
                'foreign_price_unit': order.price_unit * value_rate,
                'foreign_subtotal': order.price_subtotal * value_rate,
            })

    # validar que el precio unitario no sea mayor al costo del producto, basado en la configuracion
    @api.onchange('price_unit', 'product_id')
    def onchange_price_unit_check_cost(self):
        for l in self:
            if self.env['ir.config_parameter'].sudo().get_param('not_cost_higher_price_sale') and l.price_unit and l.product_id:
                _logger.info("costo del producto %s",
                             l.product_id.standard_price)
                _logger.info("precio unitario %s", l.price_unit)
                if l.price_unit <= l.product_id.standard_price and l.product_id.type == 'product':  # solo aplica a almacenables
                    raise ValidationError(
                        "Precio unitario no puede ser menor o igual al costo del producto")

    @api.onchange('product_uom_qty', 'product_uom', 'order_id.warehouse_id')
    def _onchange_product_id_check_availability(self):
        # _logger.info("_onchange_product_id_check_availability %s")
        # _logger.info(self.product_id)
        # _logger.info(self.product_uom_qty)
        # _logger.info(self.product_uom)
        # _logger.info(self.order_id.warehouse_id)
        # _logger.info(self.warehouse_id)

        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            #self.product_packaging = False
            return {}
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            product = self.product_id.with_context(
                warehouse=self.order_id.warehouse_id.id,
                lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US'
            )
            product_qty = self.product_uom._compute_quantity(
                self.product_uom_qty, self.product_id.uom_id)
            _logger.info("float_compare(product.free_qty, product_qty, precision_digits=precision) %s", float_compare(
                product.free_qty, product_qty, precision_digits=precision))
            if float_compare(product.free_qty, product_qty, precision_digits=precision) == -1:
                message = _('Planeas vender %s %s de %s pero solo tienes %s %s disponibles en %s.') % \
                    (self.product_uom_qty, self.product_uom.name, self.product_id.name,
                     product.free_qty, product.uom_id.name, self.order_id.warehouse_id.name)
                # We check if some products are available in other warehouses.
                if float_compare(product.free_qty, self.product_id.free_qty, precision_digits=precision) == -1:
                    message += _('\nExisten %s %s disponible entre todos los almacenes.\n\n') % \
                        (self.product_id.free_qty, product.uom_id.name)
                    for warehouse in self.env['stock.warehouse'].search([]):
                        quantity = self.product_id.with_context(
                            warehouse=warehouse.id).free_qty
                        if quantity > 0:
                            message += "%s: %s %s\n" % (warehouse.name,
                                                        quantity, self.product_id.uom_id.name)
                warning_mess = {
                    'title': _('No hay suficiente inventario!'),
                    'message': message
                }
                self.product_uom_qty = 0
                return {'warning': warning_mess}
        return {}

    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
                                          readonly=True, store=True,
                                          help='Utility field to express amount currency')
    foreign_price_unit = fields.Monetary(
        string='Precio Alterno', store=True, readonly=True, compute='_amount_all_foreign', tracking=4)
    foreign_subtotal = fields.Monetary(
        string='Subtotal Alterno', store=True, readonly=True, compute='_amount_all_foreign', tracking=4)
    foreign_currency_id = fields.Many2one('res.currency', default=default_alternate_currency,
                                          tracking=True)
