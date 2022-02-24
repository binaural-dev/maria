from odoo import models, api


class ReportRetentionIvaVoucher(models.AbstractModel):
    _name = "report.binaural_reporte_fiscal.retention_iva_voucher"


    @api.model
    def render_html(self, docids, data=None):
        data = self.env["ir.config_parameter"].sudo().get_param("curreny_foreign_id")
        docargs = {
            "doc_ids": self.ids,
            "doc_model": self.model,
            "data": data,
        }
        return self.env["report"].render("binaural_reporte_fiscal.retention_iva_voucher")
