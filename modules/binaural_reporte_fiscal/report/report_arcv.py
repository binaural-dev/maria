import time
import logging
_logger = logging.getLogger(__name__)

from odoo import models, fields, api


class ArcvReport(models.AbstractModel):
    _name = 'report.binaural_reporte_fiscal.report_template_arcv'
    _description = "Report AR-CV"

    @api.model
    def _get_report_values(self, docids, data=None):
        foreign_currency_id = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
        currency_id = 2 if foreign_currency_id == 3 else 3
        foreign_currency_id = self.env['res.currency'].browse(foreign_currency_id)

        currency_id = self.env['res.currency'].browse(currency_id)

        _logger.info(f"Currency_id: {currency_id}")

        return {
            'doc_ids': docids,
            'doc_model': data['model'],
            'docs': data['form'],
            'data': data,
            'foreign_currency_id': foreign_currency_id,
            'currency_id': currency_id,
        }
