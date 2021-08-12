# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountJournalBinauralFacturacion(models.Model):
    _inherit = "account.journal"

    fiscal = fields.Boolean(string="Fiscal", default=False, tracking=100)
