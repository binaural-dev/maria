# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.base.tests.common import HttpCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestOtraPueba(HttpCase):
    def test_01_prueba_ui(self):
        self.start_tour("/web", 'test_ventas', login = "admin")
