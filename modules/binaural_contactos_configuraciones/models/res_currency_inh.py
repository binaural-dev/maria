# -*- coding: utf-8 -*-
import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class ResCurrencyInh(models.Model):
    _inherit = 'res.currency'

    def _convert(self, from_amount, to_currency, company, date, round=True, byrate=1):
        """Returns the converted amount of ``from_amount``` from the currency
           ``self`` to the currency ``to_currency`` for the given ``date`` and
           company.

           :param company: The company from which we retrieve the convertion rate
           :param date: The nearest date from which we retriev the conversion rate.
           :param round: Round the result or not
        """
        self, to_currency = self or to_currency, to_currency or self
        assert self, "convert amount from unknown currency"
        assert to_currency, "convert amount to unknown currency"
        assert company, "convert amount from unknown company"
        assert date, "convert amount from unknown date"
        # apply conversion rate
        if self == to_currency:
            to_amount = from_amount
        elif byrate != 1:
            to_amount = from_amount * self._get_conversion_byrate(self, to_currency, company, date, byrate)
        else:
            to_amount = from_amount * self._get_conversion_rate(self, to_currency, company, date)
        # apply rounding
        return to_currency.round(to_amount) if round else to_amount


    @api.model
    def _get_conversion_byrate(self, from_currency, to_currency, company, date, byrate):
        currency_rates = (from_currency + to_currency)._get_rates(company, date)
        currency_rates.update({from_currency.id: byrate})
        res = currency_rates.get(to_currency.id) / currency_rates.get(from_currency.id)
        _logger.info(res)
        return res

