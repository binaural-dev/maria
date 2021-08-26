# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountRetentionBinauralFacturacionReport(models.Model):
    _inherit = "account.retention"

    def islr_report(self):
        if self.ensure_one():
            return self.env.ref('binaural_reporte_fiscal.retention_iva_voucher').report_action(self)

    def get_signature(self):
        config = self.env['signature.config'].search([('active', '=', True)], limit=1)
        if config and config.signature:
            return config.signature
        else:
            return False

    def action_retention_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('binaural_reporte_fiscal',
                                                         'email_template_edi_account_retention')[1]
        template_id = self.env['mail.template'].browse(template_id).id
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'account.retention',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            # 'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang),
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
