from odoo import models, fields, api, _


class AccountFinancialConfigReportLineBinaural(models.Model):
    _name = "account.financial.config.report.line"
    _rec_name = 'nro_nivel'

    nro_nivel = fields.Integer(string="Nro de Nivel")
    code_length = fields.Integer(string="Longitud de código de cuenta")

