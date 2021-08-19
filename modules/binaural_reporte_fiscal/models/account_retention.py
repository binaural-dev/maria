# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountRetentionBinauralFacturacionReport(models.Model):
    _inherit = "account.retention"

    def islr_report(self):
        if self.ensure_one():
            return self.env.ref('binaural_reporte_fiscal.retention_iva_voucher').report_action(self)

    def get_signature(self):
        config = self.env['signature.config'].search([('active', '=', True)], limit=1)
        if config and config.signature:
            return config.signature
        else:
            return False
