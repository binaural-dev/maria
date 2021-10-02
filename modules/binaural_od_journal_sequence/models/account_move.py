# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class AccountMoveExt(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        for move in self:
            if move.name == '/' and (move.move_type not in ['in_invoice', 'in_refund'] or move.is_contingence):
                sequence = move._get_sequence()
                if not sequence:
                    raise UserError(_('Please define a sequence on your journal.'))
                move.name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
        res = super(AccountMoveExt, self)._post(soft=True)
        return res
