# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.base.tests.common import HttpCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestPruebaFacturacion(HttpCase):
    def test_01_prueba_facturacion(self):
        self.start_tour("/web", 'test_facturacion', login = "admin")
