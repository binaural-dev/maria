from unicodedata import decimal
from odoo import api, fields, models
from odoo.tools import float_is_zero
import logging
_logger = logging.getLogger(__name__)

class CalculateCurrency(models.Model):
    _inherit = "res.currency.rate"

    vef_rate = fields.Float(string="Valor en BS", default=0.00, digits=(12, 2))

    @api.onchange('vef_rate')
    def _onchange_rate(self):
        decimal_function = self.env['decimal.precision'].search([('name', '=', 'decimal_quantity')])
        if not float_is_zero(self.vef_rate, 10):
            self.rate = decimal_function.getCurrencyValue(rate=self.vef_rate, base_currency='VEF', foreign_currency='USD')
