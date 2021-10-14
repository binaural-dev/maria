# EJEMPLO DE PRUEBAS EN PHANTOMJS ----- LANZADOR CON PYTHON
# EN ODOO +14 SE UTILIZA START_TOUR O BROWSER_TOUR 

from odoo.addons.base.tests.common import HttpCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestUi(odoo.tests.HttpCase):
    def test_01_accouting_retenciones(self):
        link = '/web'
        self.start_tour(link, 'test_ventas', login = "admin")



