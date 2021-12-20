# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountFiscalyearClosingAbstract(models.AbstractModel):
    _name = "account.fiscalyear.closing.abstract"
    _description = "Account fiscalyear closing abstract"

    name = fields.Char(string="Descripción", required=True)
    company_id = fields.Many2one(
        comodel_name='res.company', string="Compañía", ondelete='cascade',
    )
    check_draft_moves = fields.Boolean(
        string="Verificar movimientos en borrador", default=True,
        help="Checks that there are no draft moves on the fiscal year "
             "that is being closed. Non-confirmed moves won't be taken in "
             "account on the closing operations.",
    )


class AccountFiscalyearClosingConfigAbstract(models.AbstractModel):
    _name = "account.fiscalyear.closing.config.abstract"
    _description = "Account fiscalyear closing config abstract"
    _order = "sequence asc, id asc"

    name = fields.Char(string="Descripción", required=True)
    sequence = fields.Integer(string="Secuencia", index=True, default=1)
    code = fields.Char(string="Código único", required=True)
    inverse = fields.Char(
        string="Configuración inversa",
        help="Configuration code to inverse its move",
    )
    move_type = fields.Selection(
        selection=[
            ('closing', 'Clausura'),
            ('opening', 'Apertura'),
            ('loss_profit', 'Ganancias y Pérdidas'),
            ('other', 'Otro'),
        ], string="Tipo de movimiento", default='closing',
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal", string="Diario",
    )
    closing_type_default = fields.Selection(
        selection=[
            ('balance', 'Balance'),
            ('unreconciled', 'No reconciliado'),
        ], string="Tipo de cierre predeterminado", required=True, default='balance',
    )


class AccountFiscalyearClosingMappingAbstract(models.AbstractModel):
    _name = "account.fiscalyear.closing.mapping.abstract"
    _description = "Account fiscalyear closing mapping abstract"

    name = fields.Char(string="Descripción")


class AccountFiscalyearClosingTypeAbstract(models.AbstractModel):
    _name = "account.fiscalyear.closing.type.abstract"
    _description = "Account fiscalyear closing type abstract"

    closing_type = fields.Selection(
        selection=[
            ('balance', 'Balance'),
            ('unreconciled', 'No reconciliado'),
        ], string="Tipo de cierre predeterminado", required=True,
        default='unreconciled',
    )
    account_type_id = fields.Many2one(
        comodel_name='account.account.type', string="Tipo de cuenta",
        required=True,
    )
