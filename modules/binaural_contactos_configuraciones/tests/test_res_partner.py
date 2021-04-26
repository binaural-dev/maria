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
        f.prefix_vat = 'v'
        f.vat = '21397845'
        f.type_person_ids = self.ref('binaural_contactos_configuraciones.demo_type_person_0')
        with self.assertRaises(Exception):
            f.save()

