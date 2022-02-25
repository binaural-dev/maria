from odoo import api, models


class ReportRetentionIvaVoucher(models.AbstractModel):
    _name = "report.binaural_reporte_fiscal.template_retention_iva_voucher"


    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get("active_model")
        docs = self.env["account.retention"].browse(docids)
        return {
            "docids": docids,
            "doc_model": "account.retention",
            "get_digits": self.get_digits(),
            "docs": docs,
        }

    def get_digits(self):
        currency_foreign_id = self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id')
        decimal_places = self.env["res.currency"].search([("id", '=', currency_foreign_id)]).decimal_places
        return decimal_places
