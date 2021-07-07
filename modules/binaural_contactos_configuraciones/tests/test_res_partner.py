# -*- coding: utf-8 -*-

from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tests.common import Form


class TestResPartnerBinaural(TransactionCase):

    def setUp(self):
        super(TestResPartnerBinaural, self).setUp()

    def test_form_required_field(self):
        f = Form(self.env['res.partner'])
        f.name = "Ana"
        f.prefix_vat = 'V'
        f.vat = '21397845'
        f.type_person_ids = self.ref('binaural_contactos_configuraciones.demo_type_person_0')
        with self.assertRaises(Exception):
            f.save()
    def test_set_city(self):
        partner_id = self.env.ref('base.partner_demo')
        partner_id.write({
            'country_id': self.env.ref('base.ve'),
            'state_id': self.env.ref('binaural_contactos_configuraciones.demo_res_country_state_0'),
            'city_id': self.env.ref('binaural_contactos_configuraciones.demo_res_country_city_0'),
        })
        self.assertEqual(partner_id.city_id.name, partner_id.city, msg='El campo ciudad es distinto a la ciudad seleccionada')
