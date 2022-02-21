from odoo.addons.base.tests.common import SavepointCaseWithUserDemo
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)

@tagged('post_install', '-at_install')
class DecimalPrecisionTestCase2(SavepointCaseWithUserDemo):

    def testGetCurrencyValue(self):
        precision = self.env['decimal.precision'].search(
            [('name', '=', 'decimal_quantity')])

        with self.assertRaises(UserError):
            precision.getCurrencyValue()

        with self.assertRaises(UserError):
            precision.getCurrencyValue(
                base_currency='VEF', foreign_currency='USD')

        with self.assertRaises(UserError):
            precision.getCurrencyValue(
                rate=4.61, base_currency='VEF', foreign_currency='VEF')

        with self.assertRaises(UserError):
            precision.getCurrencyValue(
                rate=4.61, base_currency='asd', foreign_currency='VEF')

        with self.assertRaises(UserError):
            precision.getCurrencyValue(
                rate=4.61, base_currency='USD', foreign_currency='asd')

        with self.assertRaises(UserError):
            precision.getCurrencyValue(
                rate=4.61, base_currency='USD', foreign_currency='VEF', operation_type='asd')
            
        val = 4.61

        rate = precision.getCurrencyValue(rate=val, base_currency='VEF', foreign_currency='USD', operation_type='FORM')
        self.assertEqual(rate, truncate(val, precision.digits))
        
        rate = precision.getCurrencyValue(rate=val, base_currency='USD', foreign_currency='VEF', operation_type='CALC')
        
        self.assertEqual(rate, truncate(val,precision.digits))
        
        
        rate = precision.getCurrencyValue(rate=val, base_currency='VEF', foreign_currency='USD', operation_type='CALC')
        
        presupuesto = val*1000
        
        self.assertEqual(rate, truncate(1/val, precision.digits))
        
        self.assertEqual(float_round(rate *presupuesto ,2),1000)
        
        val = 4001232.37
        currency = 1100907.27
        
        rate = precision.getCurrencyValue(val, base_currency='VEF', foreign_currency='USD', operation_type='CALC')
        presupuesto = val*currency
        
        self.assertEqual(float_round(rate *presupuesto,2),currency)
        
        val = 10001232.37
        currency = 1100907.27
        
        rate = precision.getCurrencyValue(val, base_currency='VEF', foreign_currency='USD', operation_type='CALC')
        presupuesto = val*currency
        
        self.assertEqual(float_round(rate *presupuesto,2),currency)
        
        val = 10001232.37
        currency = 1109797.27
        
        rate = precision.getCurrencyValue(val, base_currency='VEF', foreign_currency='USD', operation_type='CALC')
        
        presupuesto = val*currency
        
        self.assertEqual(float_round(rate *presupuesto,2),currency)
        
        val = 10001232.37
        currency = 1100907.27
        
        rate = precision.getCurrencyValue(currency, base_currency='USD', foreign_currency='VEF', operation_type='CALC')
        presupuesto = val * currency
        
        self.assertEqual(rate * val, presupuesto)
        
        

def truncate(num, n):
    integer = int(num * (10**n))/(10**n)
    return float(integer)
        