# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountRetentionBinauralFacturacionReport(models.Model):
    _inherit = "account.retention"

    def islr_report(self):
        print("------------------------>", self.ensure_one())
        iva = 0
        if self.ensure_one():
            print("paso", self.retention_line.invoice_id.amount_by_group[-1])
            if self.retention_line.invoice_id.amount_by_group[-1][0] == 'IVA 0%':
                iva = self.retention_line.invoice_id.amount_by_group[-1][1]
            return self.env.ref('binaural_reporte_fiscal.retention_iva_voucher').report_action(self)

    def get_signature(self):
        config = self.env['signature.config'].search([('active', '=', True)], limit=1)
        if config and config.signature:
            return config.signature
        else:
            return False
