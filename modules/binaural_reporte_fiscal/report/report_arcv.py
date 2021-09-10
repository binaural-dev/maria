import time

from odoo import models, fields, api


class ArcvReport(models.AbstractModel):
    _name = 'report.binaural_reporte_fiscal.report_template_arcv'
    _description = "Report AR-CV"

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': data['model'],
            'docs': data['form'],
            'data': data,
        }