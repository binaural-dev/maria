from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools import float_repr,float_is_zero

import logging
_logger = logging.getLogger(__name__)


class InheritedDecimalPrecision(models.Model):
    _inherit = 'decimal.precision'
    _description = 'Decimal Precision'

    def getCurrencyValue(self, rate=None, base_currency=None, foreign_currency=None, operation_type="CALC"):

        if rate == None or base_currency == None or foreign_currency == None:
            raise UserError(
                "Debe proporcionar rate, base_currency y foreign_currency para realizar la operacion")

        if foreign_currency not in ['VEF', 'USD'] or base_currency not in ['VEF', 'USD']:
            raise UserError(
                "Esta accion solo recibe monedas USD o VEF")

        if base_currency == foreign_currency:
            raise UserError(
                "base_currency y foreign_currency no deben ser iguales")

        if operation_type not in ["FORM", "CALC"]:
            raise UserError(
                "Debe enviar 'FORM' para operaciones de formulario o 'CALC' para realizar calculos en operation_type")

        if float_is_zero(rate, 10):
            return 0.0

        if operation_type == 'CALC':
            if base_currency == 'VEF':
                return float(float_repr(1/rate, self.digits))
            else:
                return float(float_repr(rate, 2))
        else:
            return float(float_repr(rate, 2))
