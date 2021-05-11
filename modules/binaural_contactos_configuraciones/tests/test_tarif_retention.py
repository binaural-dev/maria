# -*- coding: utf-8 -*-

from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tests.common import Form


class TestTarifRetention(TransactionCase):

    def setUp(self):
        super(TestTarifRetention, self).setUp()
        self.tarif_1 = self.env['tarif.retention'].create({
                'name': '1% - (Bs. 1.250,00 )',
                'percentage': 1.00,
                'sustract_money': 0.00,
                'apply_subtracting': True,
                'acumulative_rate': False,
                'status': True,
<<<<<<< HEAD
                'tax_unit_ids': self.env.ref('binaural_contactos_configuraciones.demo_tax_unit_1')
=======
                'tax_unit_ids': self.ref('binaural_contactos_configuraciones.demo_tax_unit_1')
>>>>>>> 6595a8a053ee3c095b79e4558031a7eddfac8e8f
            })

        self.tarif_2 = self.env['tarif.retention'].create({
                'name': '2%',
                'percentage': 2.00,
                'sustract_money': 0.00,
                'apply_subtracting': False,
                'acumulative_rate': False,
                'status': True,
<<<<<<< HEAD
                'tax_unit_ids': self.env.ref('binaural_contactos_configuraciones.demo_tax_unit_1')
            })
        
        self.tax_unit = self.env['tax.unit'].create({
                'name': '2000,00 UT',
                'value': 2000,
                'status': True,
=======
                'tax_unit_ids': self.ref('binaural_contactos_configuraciones.demo_tax_unit_1')
>>>>>>> 6595a8a053ee3c095b79e4558031a7eddfac8e8f
            })

    def test_save_tarif_retencion(self):
        """
            Validar que se registre las tarifas de retenciones
            :return:
        """
        tarif_3 = self.env['tarif.retention'].create({
            'name': 'T - 3(Acumulativo)',
            'percentage': 0.00,
            'sustract_money': 0.00,
            'apply_subtracting': False,
            'acumulative_rate': True,
            'status': True,
<<<<<<< HEAD
            'tax_unit_ids': self.env.ref('binaural_contactos_configuraciones.demo_tax_unit_1'),
=======
            'tax_unit_ids': self.ref('binaural_contactos_configuraciones.demo_tax_unit_1'),
>>>>>>> 6595a8a053ee3c095b79e4558031a7eddfac8e8f
            'acumulative_rate_ids': [(0, 0, {
                'name': '0 - 3000 UT',
                'percentage': 15.00,
                'sustract_ut': 0.00,
                'since': 0.00,
                'until': 3000,
            })]
        })
        self.assertEqual(self.tarif_1.name, '1% - (Bs. 1.250,00 )', msg='No se pudo crear la tarifa cuando aplica sustraendo')
        self.assertEqual(self.tarif_2.name, '2%', msg='No se pudo crear la tarifa cuando no aplica sustraendo')
        self.assertEqual(tarif_3.name, 'T - 3(Acumulativo)', msg='No se pudo crear la tarifa de retencion cuando aplica tarifa acumulada')

        with self.assertRaises(ValidationError):
            self.tarif_1.write({'percentage': -10})

    def test_required_field(self):
<<<<<<< HEAD
        tarif = self.env['tarif.retention'].create({
            'name': 'T - 4(Acumulativo)',
            'percentage': 1.00,
            'sustract_money': 0.00,
            'apply_subtracting': False,
            'acumulative_rate': True,
            'status': True,
            'tax_unit_ids': self.env.ref('binaural_contactos_configuraciones.demo_tax_unit_1'),
            'acumulative_rate_ids': [(0, 0, {
                'name': '0 - 4000 UT',
                'percentage': 15.00,
                'sustract_ut': 0.00,
                'since': 0.00,
                'until': 4000,
            })]
        })
        self.assertNotEqual(len(tarif.acumulative_rate_ids), 0, msg='Debe agregar al menos una linea de tarifa acumulada')
=======
        with self.assertRaises(ValidationError):
            tarif = self.env['tarif.retention'].create({
                'name': 'T - 4(Acumulativo)',
                'percentage': 0.00,
                'sustract_money': 0.00,
                'apply_subtracting': False,
                'acumulative_rate': True,
                'status': True,
                'tax_unit_ids': self.ref('binaural_contactos_configuraciones.demo_tax_unit_1')
            })
            tarif._check_data_acumulative()
>>>>>>> 6595a8a053ee3c095b79e4558031a7eddfac8e8f

    def test_form_required_field(self):
        f = Form(self.env['tarif.retention'])
        f.name = "7%"
        with self.assertRaises(Exception):
            f.save()
            
    def test_check_amount_sustract(self):
        f = Form(self.env['tarif.retention'])
        f.name = "Aplica sustraendo 7%"
        f.percentage = 7
        f.apply_subtracting = True
        f.acumulative_rate = False,
<<<<<<< HEAD
        f.tax_unit_ids = self.env.ref('binaural_contactos_configuraciones.demo_tax_unit_1')
=======
        f.tax_unit_ids = self.ref('binaural_contactos_configuraciones.demo_tax_unit_1')
>>>>>>> 6595a8a053ee3c095b79e4558031a7eddfac8e8f
        so = f.save()
        self.assertEqual(int(so.amount_sustract), 8750, msg='Error e el calculo del sustraendo')
        so.apply_subtracting = False
        so.write({'apply_subtracting': False})
        self.assertEqual(int(so.amount_sustract), 0, msg='Error e el calculo del sustraendo')
