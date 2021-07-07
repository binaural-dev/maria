# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountJournalBinauralContactos(models.Model):
    _inherit = 'account.journal'

    journal_contingence = fields.Boolean(default=False, string="Contingencia")