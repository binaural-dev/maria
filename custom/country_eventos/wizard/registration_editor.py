from odoo import models, fields, api, exceptions, _, http


class RegistrationEditorCountryExtend(models.TransientModel):
    _inherit = "registration.editor"

    def action_make_registration(self):
        self.ensure_one()
        for registration_line in self.event_registration_ids:
            values = registration_line.get_registration_data()
            if registration_line.registration_id:
                registration_line.registration_id.write(values)
            else:
                self.env['event.registration'].create(values)
        if self.env.context.get('active_model') == 'sale.order':
            for order in self.env['sale.order'].browse(self.env.context.get('active_ids', [])):
                order.order_line._update_registrations(confirm=True)
        return {'type': 'ir.actions.act_window_close'}
