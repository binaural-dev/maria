from odoo import models, fields, api, _
from collections import OrderedDict


class AccountReportBinaural(models.AbstractModel):
    _inherit = 'account.report'

    @api.model
    def _get_options(self, previous_options=None):
        """
        Obtenemos las opciones de moneda,
        verificamos la opciones anteriores o agregamos las opciones si no existen
        """
        alternate_currency = int(self.env['ir.config_parameter'].sudo().get_param('curreny_foreign_id'))
        alternate_currency = self.env['res.currency'].browse(alternate_currency)
        handlers = OrderedDict({'currency': [
            {'name': alternate_currency.name, 'id': alternate_currency.id, 'selected': False},
            {'name': self.env.user.company_id.currency_id.name, 'id': self.env.user.currency_id.id, 'selected': True}]}
        )
        current_options = super(AccountReportBinaural, self)._get_options(previous_options)

        for key, handler in handlers.items():
            if previous_options:
                currency_previus = previous_options.get('currency', False)
            else:
                currency_previus = False

            if currency_previus:
                previous_handler_value = previous_options[key]
            else:
                previous_handler_value = handler
            current_options[key] = previous_handler_value
        return current_options
