# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions
import logging

logger = logging.getLogger(__name__)


class ResConfigSettingsEvent(models.TransientModel):
    _inherit = 'res.config.settings'

    qty_max_to_day = fields.Integer(string='Cantidad Máxima de entradas al dia', required=True, default=3)
    qty_max_to_mounth = fields.Integer(string='Cantidad Máxima de entradas al mes por invitado', required=True, default=5)

    def set_values(self):
        super(ResConfigSettingsEvent, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('qty_max_to_day', self.qty_max_to_day)
        self.env['ir.config_parameter'].sudo().set_param('qty_max_to_mounth', self.qty_max_to_mounth)

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsEvent, self).get_values()
        res['qty_max_to_day'] = int(self.env['ir.config_parameter'].sudo().get_param('qty_max_to_day'))
        res['qty_max_to_mounth'] = int(self.env['ir.config_parameter'].sudo().get_param('qty_max_to_mounth'))
        return res
