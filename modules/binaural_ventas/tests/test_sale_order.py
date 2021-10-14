# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
# from odoo.addons.test_module.helpers import string

class StringHelperTest(TransactionCase):

	def test_number_equal(self):
		error = 'Algo no salio bien'
		sample_str = 6
		sample_str_len = 6
		self.assertEqual(sample_str_len, sample_str, error)	
		print('Todo bien por aca')