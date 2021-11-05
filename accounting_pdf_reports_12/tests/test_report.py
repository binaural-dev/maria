# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestReport(TransactionCase):

    print("----------------------TEST REPORT ----------------------------------")

    def setUp(self):
        super(TestReport, self).setUp()
        self.report = self.env['report.accounting_pdf_reports.report_financial']

    def test_report(self):
        docids = False
        x = self.report._get_report_values(docids)
        print(x.data)
        print("FUNCION")
