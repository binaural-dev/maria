# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _, http
import werkzeug
from odoo.http import request
from odoo.addons.website_event_sale.controllers.main import WebsiteEventSaleController
from odoo.addons.website_event.controllers.main import WebsiteEventController
from datetime import datetime, timedelta, date


class WebsiteEventControllerExtend(WebsiteEventController):
    
    @http.route(
        ['''/event/<model("event.event", "[('website_id', 'in', (False, current_website_id))]"):event>/register'''],
        type='http', auth="public", website=True, sitemap=False)
    def event_register(self, event, **post):
        if not event.can_access_from_current_website():
            raise werkzeug.exceptions.NotFound()
        user_id = request.env['res.users'].search([('id', '=', request.env.context.get('uid'))])
        cfr_search = request.env['frecuent.partner.relation'].search([('partner_id', '=', user_id.partner_id.id)])
        cf = []
        for x in cfr_search:
            val = {
                'prefix_vat': x.frecuent_partner_id.prefix_vat,
                'vat': x.frecuent_partner_id.vat,
                'email': x.frecuent_partner_id.email,
                'phone': x.frecuent_partner_id.phone,
                'name': x.frecuent_partner_id.name,
                'active': x.active,

            }
            cf.append(val)
        values = {
            'event': event,
            'valid': True,
            'msg': '',
            'main_object': event,
            'range': range,
            'registrable': event.sudo()._is_event_registrable(),
            'contacts': cf,
        }
        return request.render("website_event.event_description_full", values)
    
    @http.route(['/event/<model("event.event"):event>/registration/new'], type='json', auth="public", methods=['POST'],
                website=True)
    def registration_new(self, event, **post):
        tickets = self._process_tickets_details(post)
        if not tickets:
            return False
        return request.env['ir.ui.view'].render_template("website_event.registration_attendee_details",
                                                         {'tickets': tickets, 'event': event})


class WebsiteEventSaleControllerExtend(WebsiteEventSaleController):

    @http.route()
    def event_register(self, event, **post):
        event = event.with_context(pricelist=request.website.id)
        if not request.context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            if pricelist:
                event = event.with_context(pricelist=pricelist.id)
        return super(WebsiteEventSaleControllerExtend, self).event_register(event, **post)
    
    def _process_tickets_details(self, data):
        ticket_post = {}
        for key, value in data.items():
            if not key.startswith('nb_register') or '-' not in key:
                continue
            items = key.split('-')
            if len(items) < 2:
                continue
            ticket_post[int(items[1])] = int(value)
        tickets = request.env['event.event.ticket'].browse(tuple(ticket_post))
        return [{'id': ticket.id, 'name': ticket.name, 'quantity': ticket_post[ticket.id], 'price': ticket.price} for
                ticket in tickets if ticket_post[ticket.id]]

    def valid(self, date1, partner, registrations):
        ticket = ''
        count_reg = 0
        partner_id = request.env['res.partner'].search(
            [('id', '=', partner)])
        if partner_id.can_access_club is False:
            return False
        for cr in registrations:
            if 'ticket_id' in list(cr.keys()):
                ticket = cr.get('ticket_id')
        event_id = request.env['event.event.ticket'].search(
            [('id', '=', ticket)])
        if event_id.event_id.event_type == 'invitations':
            len_entries_day = request.env['event.registration'].search(
                [('date_invitation', '=', date1),
                 ('partner_id', '=', partner)])
            qty_max_to_day = int(request.env['ir.config_parameter'].sudo().get_param('qty_max_to_day'))
            for cr in registrations:
                if 'ticket_id' in list(cr.keys()):
                    count_reg += 1
            entries_day = len(len_entries_day) + count_reg
            if entries_day > qty_max_to_day:
                return False
            date_parameter = datetime.strptime(str(date1), '%Y-%m-%d')
            date_start_date = '%s-%s-%s' % (date_parameter.year, date_parameter.month, 1)
            if date_parameter.month != 12:
                date_end_date = '%s-%s-%s' % (date_parameter.year, date_parameter.month + 1, 1)
            else:
                date_end_date = '%s-%s-%s' % (date_parameter.year, date_parameter.month, 31)
            qty_max_to_mounth = int(request.env['ir.config_parameter'].sudo().get_param('qty_max_to_mounth'))
            for x in registrations:
                if 'ticket_id' in list(x.keys()):
                    len_entries_mounth = request.env['event.registration'].search(
                        [('date_invitation', '>=', date_start_date),
                         ('date_invitation', '<', date_end_date),
                         ('partner_id', '=', partner),
                         ('vat', '=', x['vat']),
                         ('state', 'not in', ['cancel']),
                         ])
                    entries_mounth = len(len_entries_mounth) + 1
                    if entries_mounth > qty_max_to_mounth:
                        return False
                    else:
                        return True

    @http.route()
    def registration_confirm(self, event, **post):
        order = request.website.sale_get_order(force_create=1)
        attendee_ids = set()
        valid = False
        registrations = self._process_registration_details(post)
        user_id = request.env['res.users'].search([('id', '=', request.env.context.get('uid'))])
        valid = self.valid(registrations[0].get('date_invitation'), user_id.partner_id.id, registrations)
        if valid:
            for registration in registrations:
                if 'ticket_id' in list(registration.keys()):
                    if 'contact' in list(registration.keys()):
                        cfr_search = False
                        fp = False
                        cf_search = request.env['frecuent.partner'].search([('vat', '=', registration['vat'])])
                        if cf_search:
                            cfr_search = request.env['frecuent.partner.relation'].search(
                                [('frecuent_partner_id', '=', cf_search.id),
                                 ('partner_id', '=', user_id.partner_id.id)])
                        if not cf_search:
                            cf = {
                                'prefix_vat': registration['prefix_vat'],
                                'vat': registration['vat'],
                                'email': registration['email'],
                                'phone': registration['phone'],
                                'name': registration['name'],
                            }
                            fp = request.env['frecuent.partner'].create(cf)
                        if not cfr_search and not cf_search:
                            cf_related = {
                                'active': True,
                                'frecuent_partner_id': fp.id,
                                'partner_id': user_id.partner_id.id,
                            }
                            request.env['frecuent.partner.relation'].create(cf_related)
                        elif not cfr_search and cf_search:
                            cf_related = {
                                'active': True,
                                'frecuent_partner_id': cf_search.id,
                                'partner_id': user_id.partner_id.id,
                            }
                            request.env['frecuent.partner.relation'].create(cf_related)
                        elif cfr_search and cf_search:
                            cfr_search.write({'active': True})
                    else:
                        print('NO ES FRECUENTE')
                    if not order.validity_date:
                        order.write({'validity_date': registration['date_invitation']})
                    ticket = request.env['event.event.ticket'].sudo().browse(int(registration['ticket_id']))
                    cart_values = order.with_context(event_ticket_id=ticket.id, fixed_price=True)._cart_update(
                        product_id=ticket.product_id.id, add_qty=1, registration_data=[registration])
                    attendee_ids |= set(cart_values.get('attendee_ids', []))
                else:
                    if registration['name'] == '':
                        user_id = request.env['res.users'].search([('id', '=', request.env.context.get('uid'))])
                        print('USER')
                        print(user_id.partner_id.id)
                        partner_frec_id = request.env['frecuent.partner'].search([('vat', '=', registration['vat'])]).id
                        print('Partner_frec')
                        print(partner_frec_id)
                        relation = request.env['frecuent.partner.relation'].search(
                            [('partner_id', '=', user_id.partner_id.id), ('frecuent_partner_id', '=', partner_frec_id)])
                        print('relation update')
                        print(relation)
                        relation.write({'active': False})
                    else:
                        partner_frec_id = request.env['frecuent.partner'].search([('vat', '=', registration['vat'])])
                        partner_frec_id.write({
                            'name': registration['name'],
                            'email': registration['email'],
                            'phone': registration['phone'],
                        })
            # free tickets -> order with amount = 0: auto-confirm, no checkout
            if not order.amount_total:
                order.action_confirm()  # tde notsure: email sending ?
                attendees = request.env['event.registration'].browse(list(attendee_ids)).sudo()
                # clean context and session, then redirect to the confirmation page
                request.website.sale_reset()
                urls = event._get_event_resource_urls(list(attendee_ids))
                return request.render("website_event.registration_complete", {
                    'attendees': attendees,
                    'event': event,
                    'google_url': urls.get('google_url'),
                    'iCal_url': urls.get('iCal_url')
                })

            return request.redirect("/shop/checkout")
        else:
            is_solvent = self.can_access_club(user_id.partner_id.id)
            if is_solvent is False:
                msg = 'Debe estar solvente para registrar invitaciones!!!'
            else:
                msg = 'No puede registrar mas invitados de los permitidos por el club.!!!'
            values = {
                'event': event,
                'valid': False,
                'main_object': event,
                'msg': msg,
                'range': range,
                'registrable': event.sudo()._is_event_registrable()
            }
            return request.render("website_event.event_description_full", values)

    def can_access_club(self, partner):
        partner_id = request.env['res.partner'].search(
            [('id', '=', partner)])
        if partner_id.can_access_club is False:
            return False
        else:
            return True