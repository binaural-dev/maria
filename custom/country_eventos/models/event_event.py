# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _, http
from odoo.http import request
from datetime import date


class EventEventExtend(models.Model):
    _inherit = 'event.event'

    event_type = fields.Selection([('events', 'Eventos'), ('invitations', 'invitationes')], string="Tipo de Evento")


class EventRegistrationExtend(models.Model):
    _inherit = 'event.registration'

    date_invitation = fields.Date(string='Fecha de invitación')
    prefix_vat = fields.Selection([
        ('v', 'V'),
        ('e', 'E'),
        ('j', 'J'),
        ('g', 'G'),
        ('c', 'C'),
    ], 'Prefijo Rif', required=False, default='v')
    vat = fields.Char(string='RIF', required=False)
    state = fields.Selection([
        ('draft', 'Pago No confirmado'), ('cancel', 'Invitación Cancelada'),
        ('open', 'Pago confirmado'), ('done', 'Asistencia al Club')],
        string='Status', default='draft', readonly=True, copy=False, track_visibility='onchange')

    @api.model
    def _prepare_attendee_values(self, registration):
        """ Override to add sale related stuff """
        line_id = registration.get('sale_order_line_id')
        if line_id:
            registration.setdefault('partner_id', line_id.order_id.partner_id)
        att_data = super(EventRegistrationExtend, self)._prepare_attendee_values(registration)
        if line_id:
            att_data.update({
                'event_id': line_id.event_id.id,
                'event_ticket_id': line_id.event_ticket_id.id,
                'origin': line_id.order_id.name,
                'sale_order_id': line_id.order_id.id,
                'sale_order_line_id': line_id.id,
            })
        return att_data

    @api.model
    def create(self, vals):
        res = super(EventRegistrationExtend, self).create(vals)
        param = self.env['ir.config_parameter']
        invitation_prepaid = bool(param.sudo().get_param('invitation_prepaid'))
        if invitation_prepaid:
            res.generate_qr()
            try:
                temp_id = self.env.ref('event.event_registration_mail_template_badge')
                temp_id.send_mail(res['id'], True)
                res.action_send_badge_email()
            except:
                return
        else:
            res.confirm_registration()
            res.generate_qr()
            try:
                temp_id = self.env.ref('event.event_registration_mail_template_badge')
                temp_id.send_mail(res['id'], True)
                res.action_send_badge_email()
            except:
                return
        return res

    def cancel_invitation_due(self):
        date_now = str(date.today())
        registrations = request.env['event.registration'].search(
            [('date_invitation', '=', date_now),
             ('state', 'in', ['draft', 'open'])])
        for x in registrations:
            x.write({'state': 'cancel'})
