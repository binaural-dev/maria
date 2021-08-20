# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
import math
from datetime import date


class TxtWizard(models.TransientModel):
    _name = 'txt.wizard'
    _description = 'Declarar el IVA ante el SENIAT'

    date_start = fields.Date('Fecha de inicio', default=date.today().replace(day=1))
    date_end = fields.Date('Fecha de termino', default=date.today().replace(day=1) + relativedelta(months=1, days=-1))

    def generte_txt(self):
        print("holaaaaaaaaaaaaa")
        rentModel = self.env['library.book.rent']
        for wiz in self:
            for book in wiz.book_ids:
                rentModel.create({
                    'borrower_id': wiz.borrower_id.id,
                    'book_id': book.id
                })