# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettingBinauralContactos(models.TransientModel):
    _inherit = 'res.config.settings'

    use_retention = fields.Boolean(string="Usa Retenciones", default=False)

    account_retention_iva = fields.Many2one('account.account', 'Cuenta de Retención IVA')
    account_retention_islr = fields.Many2one('account.account', 'Cuenta de Retención ISLR')

    account_retention_receivable_client = fields.Many2one('account.account', 'Cuenta P/cobrar clientes')
    account_retention_to_pay_supplier = fields.Many2one('account.account', 'Cuenta P/pagar proveedor')

    journal_retention_client = fields.Many2one('account.journal', 'Diario de Retenciones de Clientes')
    journal_retention_supplier = fields.Many2one('account.journal', 'Diario de Retenciones de Proveedores')

    qty_max = fields.Integer(string='Cantidad Máxima', required=True, default=25)

    journal_contingence_ids = fields.Many2one('account.journal', 'Diario de Factura de Contingencia')
    curreny_foreign_id = fields.Many2one('res.currency', 'Moneda Alterna')

    @api.model
    def get_values(self):
        res = super(ResConfigSettingBinauralContactos, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            use_retention=params.get_param('use_retention'),
            account_retention_iva=int(params.get_param('account_retention_iva')),
            account_retention_islr=int(params.get_param('account_retention_islr')),
            account_retention_receivable_client=int(params.get_param('account_retention_receivable_client')),
            account_retention_to_pay_supplier=int(params.get_param('account_retention_to_pay_supplier')),
            journal_retention_client=int(params.get_param('journal_retention_client')),
            journal_retention_supplier=int(params.get_param('journal_retention_supplier')),
            qty_max=int(params.get_param('qty_max')),
            curreny_foreign_id=int(params.get_param('curreny_foreign_id')),
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('use_retention', self.use_retention)
        self.env['ir.config_parameter'].sudo().set_param('account_retention_iva', self.account_retention_iva.id)
        self.env['ir.config_parameter'].sudo().set_param('account_retention_islr', self.account_retention_islr.id)
        self.env['ir.config_parameter'].sudo().set_param('account_retention_receivable_client', self.account_retention_receivable_client.id)
        self.env['ir.config_parameter'].sudo().set_param('account_retention_to_pay_supplier', self.account_retention_to_pay_supplier.id)
        self.env['ir.config_parameter'].sudo().set_param('journal_retention_client', self.journal_retention_client.id)
        self.env['ir.config_parameter'].sudo().set_param('journal_retention_supplier', self.journal_retention_supplier.id)
        self.env['ir.config_parameter'].sudo().set_param('qty_max', self.qty_max)
        self.env['ir.config_parameter'].sudo().set_param('curreny_foreign_id', self.curreny_foreign_id.id)
        super(ResConfigSettingBinauralContactos, self).set_values()
