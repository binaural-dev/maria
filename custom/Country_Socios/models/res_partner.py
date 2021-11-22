# -*- coding: utf-8 -*-

from odoo import models, api, exceptions, fields, _

from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import timedelta


class ResPartnerAction(models.Model):
    _inherit = 'res.partner'

    def actions_active(self):
        actions = []
        partner_action = self.env['res.partner'].search([('action_number', '!=', False)])
        for x in partner_action:
            actions.append(x.action_number.number)
        return [('number', 'not in', actions)]#tesoreria es disponible para asignar
    
    def compute_solvent(self):
        partner_ids = self.env['res.partner'].search([('customer_rank', '>', 0)])
        for record in partner_ids:
            invoices = record.invoice_ids.filtered(lambda x: x.state in ['draft', 'open'])
            if len(invoices) > 0:
                record.is_solvent = False
            else:
                record.is_solvent = True

    def update_action_contact(self):
        partner_ids = self.env['res.partner'].search([('type', '=', 'contact')])
        for record in partner_ids:
            search_ind = record.display_name.find(",")
            search_ind_contact = record.display_name[search_ind+1:].find(",")
            if search_ind_contact == -1 and record.parent_id:
                record.write({'display_name': record.display_name[:search_ind+1] + '%s - ' % str(record.parent_id.action_number.number) + record.display_name[search_ind+1:]})

    def update_relationship_partner(self):
        partner_ids = self.env['res.partner'].search([('parent_id', '=', False)])
        for record in partner_ids:
            if record.type_of_member == 'action':
                record.write({'type_relation': 'partner'})
            elif record.type_of_member == 'extention':
                record.write({'type_relation': 'associated'})

    @api.onchange('action_number')
    def update_action_partner_and_contact(self):
        for record in self:
            if record.action_number:
                if record.type not in ['contact']:
                    record.write({'display_name': '%s - ' % str(record.action_number.number) + record.name})
                else:
                    for x in record.child_ids:
                        search_ind_contact = x.display_name.find("-")
                        search_ind = x.display_name.find(",")
                        x.write({'display_name': x.display_name[:search_ind + 1] + '%s - ' % str(
                            x.parent_id.action_number.number) + x.display_name[search_ind_contact + 1:]})

    def compute_solvent_list(self):
        for record in self:
            if record.parent_id:
                record.is_solvent_related = record.parent_id.is_solvent
            else:
                record.is_solvent_related = record.is_solvent

    action_number = fields.Many2one('action.partner', string='Número de Acción', domain=actions_active)
    action_number_related = fields.Many2one('action.partner', string='Accion relacionada', related='parent_id.action_number')
    is_solvent_related = fields.Boolean(string='Socio solvente', compute='compute_solvent_list')
    
    state_action = fields.Selection([
        ('active', 'Activa'),
        ('special', 'Especial'),
        ('honorary', 'Honorario'),
        ('treasury', 'Tesorería'),
    ], 'Estado de la Acción', related="action_number.state", store=True,track_visibility='onchange')

    state_partner = fields.Selection([
        ('active', 'Activo'),
        ('holder', 'Tenedor'),
        ('deceased', 'Fallecido'),
        #('discontinued', 'Suspendido'),
        ('inactive', 'Inactivo'),
    ], 'Estado', default='active', required=True,track_visibility='onchange')

    other_doc_id = fields.Char(string='Otro Documento de Identificación',track_visibility='onchange')
    
    start_date = fields.Date('Fecha de Inicio',track_visibility='onchange')
    birthday = fields.Date('Fecha de Nacimiento',track_visibility='onchange')
    age = fields.Integer('Edad')
    office_phone = fields.Char(string='Teléfono de oficina',track_visibility='onchange')
    mobile_phone_two  = fields.Char(string='Teléfono Celular Adicional',track_visibility='onchange')
    aditional_email  = fields.Char(string='Correo electrónico Adicional',track_visibility='onchange')

    type_of_member  = fields.Selection([
        ('action', 'Acción'),
        ('extention', 'Extensión')
    ], string='Tipo de socio',related="action_number.type_action", track_visibility='onchange')
    
    business_name_usufruct = fields.Char(string='Razón social Usufructo',track_visibility='onchange')
    prefix_vat_usufruct = fields.Selection([
        ('v', 'V'),
        ('e', 'E'),
        ('j', 'J'),
        ('g', 'G'),
    ], 'Prefijo Rif Usufructo', default='v',track_visibility='onchange')

    prefix_vat = fields.Selection([
        ('V', 'V'),
        ('E', 'E'),
        ('J', 'J'),
        ('G', 'G'),
        ('C', 'C'),
    ], 'Prefijo Rif', required=False, default='V')
    vat_usufruct = fields.Char(string='RIF Usufruto',track_visibility='onchange')
    address_usufruct = fields.Text(string='Dirección fiscal Usufructo',track_visibility='onchange')

    is_solvent = fields.Boolean(string='Está Solvente', default=True, track_visibility='onchange')

    member_company = fields.Char(string='Empresa')
    member_profession = fields.Many2one('country.professions', string='Profesión',track_visibility='onchange',domain=[('active','=',True)])
    member_gender = fields.Selection([
        ('male', 'Masculino'),
        ('female', 'Femenino'),
        ('other', 'Other')
    ], default="male",string="Sexo",track_visibility='onchange')
    member_marital = fields.Selection([
        ('single', 'Soltero'),
        ('married', 'Casado'),
        ('cohabitant', 'Concubinato'),
        ('widower', 'Viudo'),
        ('divorced', 'Divorciado')
    ], string='Estado Civil', default='single',track_visibility='onchange')
    member_contact_name =  fields.Char(string='Nombre y Apellido de contacto',track_visibility='onchange')
    member_contact_phone = fields.Char(String='Teléfono de contacto',track_visibility='onchange')
    member_contact_email  = fields.Char(string='Correo electrónico de contacto',track_visibility='onchange')
 
    can_access_club = fields.Boolean(string='Accesso al Club',default=True,track_visibility='onchange')
    #fecha de fin del socio
    end_date_partner = fields.Date('Fecha de vencimiento de socio',track_visibility='onchange')
    alerted_end_date_partner = fields.Boolean('Usuario alertado de vencimiento proximo')

    #carga familiar
    type_relation = fields.Selection([
        ('partner', 'Titular'),
        ('associated', 'Asociado'),
        ('wife', 'Esposa(o)'),
        ('children', 'Hijo(a)'),
        ('parents','Padres'),
        ('special_children','Hijo(a) Especial'),
    ], string='Clasificación', default=False, track_visibility='onchange')

    
    """state_family = fields.Selection([
        ('active', 'Activo'),
        ('discontinued', 'Suspendido'),
        ('inactive', 'Inactivo'),
    ], 'Estado', default='active', required=True)"""
    end_date_family = fields.Date('Fecha de vencimiento de asociación',track_visibility='onchange')
    family_reference = fields.Char(string='Referencia',track_visibility='onchange')
    
    #asociado familiar
    associate_parent = fields.Many2one('res.partner', string='Socio Padre',track_visibility='onchange')
    associate_action = fields.Many2one('action.partner', string='Número de Acción Padre',related="associate_parent.action_number",track_visibility='onchange')
    associate_childs = fields.One2many('res.partner', 'associate_parent', string='Asociados Familiar', domain=[('active', '=', True)],track_visibility='onchange')
    #campos referentes a la suspensión
    reason = fields.Text(string='Motivo')
    end_date_suspend = fields.Date(string='Fecha final de suspensión')
    start_date_suspend = fields.Date(string='Fecha inicio de suspensión')
    user_suspend = fields.Many2one('res.users',string='Usuario que suspende')
 
    
    prev_state_partner = fields.Selection([
        ('active', 'Activo'),
        ('holder', 'Tenedor'),
        ('deceased', 'Fallecido'),
        #('discontinued', 'Suspendido'),
        ('inactive', 'Inactivo'),
    ], 'Estado Anterior',default='active')

    #campos referentes a remover suspension
    user_remove_suspend = fields.Many2one('res.users',string='Usuario que removio la suspensión')
    date_remove_suspend  = fields.Date(string='Fecha en que se removio la suspensión')
    
    def _default_type_person(self):
        return self.env['type.person'].search([('state', '=',True)], limit=1).id
    
    type_person_ids = fields.Many2one('type.person', 'Tipo de Persona', track_visibility="onchange",default=_default_type_person)

    def action_transfer(self):
        for p in self:
            if p.type_of_member != 'action':
                raise exceptions.UserError("No puedes transferir un socio tenedor")
            if not p.is_solvent or not p.active:
                raise exceptions.UserError("No puedes transferir una acción en mora o inactiva")

            p.write({'active':False})#esto archivara los asociados
            p.message_post(
                subject=_("Socio archivado:(%s)") % p.name,
                body=_("Socio archivado %s el: %s, por transferencia de acción") % (
                    p.name,
                    fields.Date.today().strftime("%d/%m/%y"),
                )
            )
            try:
                values_action = {'name':p.name,'identification':str(p.prefix_vat)+str(p.vat),'date_start':p.start_date,'date_end':p.end_date_partner,'action_id':p.action_number.id,'type_operation':'unlink','name_exec':self.env.user.name,'date_exec':fields.Date.today()}
                self.env['action.partner.previous'].sudo().create(values_action)
            except Exception as e:
                print(e)

    #archivar socio al llegar a la fecha fin de la suspension
    def archive_members_auto(self):
        partners_to_remove = self.env['res.partner'].search([('active','=',True),('end_date_partner','=',fields.Date.today())])
        #fecha de fin igual a la fecha de hoy
        for p in partners_to_remove:
            p.write({'active':False})#esto archivara los asociados
            p.message_post(
                subject=_("Socio archivado:(%s)") % p.name,
                body=_("Socio archivado %s el: %s, Automaticamente") % (
                    p.name,
                    fields.Date.today().strftime("%d/%m/%y"),
                )
            )
            try:
                values_action = {'name':p.name,'identification':str(p.prefix_vat)+str(p.vat),'date_start':p.start_date,'date_end':p.end_date_partner,'action_id':p.action_number.id,'type_operation':'unlink','name_exec':self.env.user.name,'date_exec':fields.Date.today()}
                self.env['action.partner.previous'].sudo().create(values_action)
            except Exception as e:
                print(e)
    #alertar por correo de proximidad de fecha fin de accion
    def alert_end_date_members_auto(self):
        config = self.env['country.config.members'].sudo().search([('active','=',True)],limit=1)
        if not config:
            raise exceptions.UserError("No hay configuración de socios registrada por favor contacte al administrador del sistema")

        end_date_to_compare = fields.Date.today() + relativedelta(days=config.previous_days_alert_associates)
        #si la fecha de fin del socio es menor o igual a la suma de la fecha de hoy + dias de alerta quiere decir que se finaliza en ese rango de tiempo
        partners_to_alert = self.env['res.partner'].search([('parent_id','=',False),('active','=',True),('end_date_partner','<=',end_date_to_compare),('alerted_end_date_partner','=',False)])
        try:
            template = self.env.ref('Country_Socios.email_alert_end_date_partner', raise_if_not_found=False)
        except Exception as e:
            print("error enviando email",e)
            pass
        for p in partners_to_alert:
            if p.email and template:
                template.with_context(lang=p.lang,email_from=config.out_email_alert_associates,email_alert_signature=config.signature.decode("utf-8") ).send_mail(p.id, force_send=True, raise_exception=False)#True
                p.write({'alerted_end_date_partner':True})

    #write function para captar el Archivar ya que no es con funcion aparte
    def write(self, vals):
        print("valores a editar %s",vals)
        if 'active' in vals:
            for partner in self:
                if partner.parent_id.id == False:#es el padre y esta archivando
                    if vals.get('active') is False:
                        for ch in partner.child_ids:
                            ch.write({'active':False})
                        associates = self.env['res.partner'].search([('associate_parent','=',partner.id)])
                        if associates:
                            for a in associates:
                                a.write({'active':False})
                        
                        #remove users linked
                        print("eliminar link")
                        partner.write({'user_ids':[(5, 0,0)]})
                        
                        try:
                            values_action = {'name':partner.name,'identification':str(partner.prefix_vat)+str(partner.vat),'date_start':partner.start_date,'date_end':partner.end_date_partner,'action_id':partner.action_number.id,'type_operation':'unlink','name_exec':self.env.user.name,'date_exec':fields.Date.today()}
                            self.env['action.partner.previous'].sudo().create(values_action)
                        except Exception as e:
                            print(e)
                    else:
                        #reactivando
                        associates = self.env['res.partner'].search([('associate_parent','=',partner.id),('active','=',False)])
                        if associates:
                            for a in associates:
                                a.write({'active':True})
                        
                        childs = self.env['res.partner'].search([('parent_id','=',partner.id),('active','=',False)])
                        for ch in childs:
                            ch.write({'active':True})

                        try:
                            values_action = {'name':partner.name,'identification':str(partner.prefix_vat)+str(partner.vat),'date_start':partner.start_date,'date_end':partner.end_date_partner,'action_id':partner.action_number.id,'type_operation':'link','name_exec':self.env.user.name,'date_exec':fields.Date.today()}
                            self.env['action.partner.previous'].sudo().create(values_action)
                        except Exception as e:
                            print(e)

                        #linked user if email is same
                        user = self.env['res.users'].search([('login','=',partner.email)],limit=1)
                        if user:
                            partner.write({'user_ids':[(4,user.id,0)]})

        if 'action_number' in vals:
            try:
                action_obj = self.env['action.partner'].browse(vals.get('action_number'))
                if action_obj:
                    #link new
                    values_action_a = {'name':self.name,'identification':str(self.prefix_vat)+str(self.vat),'date_start':self.start_date,'date_end':self.end_date_partner,'action_id':action_obj.id,'type_operation':'link','name_exec':self.env.user.name,'date_exec':fields.Date.today()}
                    self.env['action.partner.previous'].sudo().create(values_action_a)
                    
                    #unlink previos
                    values_action_u = {'name':self.name,'identification':str(self.prefix_vat)+str(self.vat),'date_start':self.start_date,'date_end':self.end_date_partner,'action_id':self.action_number.id,'type_operation':'unlink','name_exec':self.env.user.name,'date_exec':fields.Date.today()}
                    self.env['action.partner.previous'].sudo().create(values_action_u)
            except Exception as e:
                print(e)
        print("self a editar",self.name)
        return super(ResPartnerAction, self).write(vals)
        
    @api.model
    def _commercial_fields(self):
        """ Returns the list of fields that are managed by the commercial entity
        to which a partner belongs. These fields are meant to be hidden on
        partners that aren't `commercial entities` themselves, and will be
        delegated to the parent `commercial entity`. The list is meant to be
        extended by inheriting classes. """
        return ['credit_limit'] #'vat', 
        
    @api.model
    def create(self,vals):
        if vals.get('type_relation') == 'children' and vals.get('age') >= 25:
            raise exceptions.UserError(
                "No pueden registrarse hijos con edad superior o igual a 25 años")

        p_vat = False
        if 'vat' in vals:
            p_vat = vals.get('vat',False)
        if 'action_number' in vals:
            try:
                action_obj = self.env['action.partner'].browse(vals.get('action_number'))
                if action_obj:
                    values_action = {'name':vals.get('name'),'identification':str(vals.get('prefix_vat'))+str(vals.get('vat')),'date_start':vals.get('start_date',fields.Date.today()),'date_end':vals.get('end_date_partner',fields.Date.today()),'action_id':action_obj.id,'type_operation':'link','name_exec':self.env.user.name,'date_exec':fields.Date.today()}
                    self.env['action.partner.previous'].sudo().create(values_action)
            except Exception as e:
                    print(e)
        partner = super(ResPartnerAction, self).create(vals)
        if partner and p_vat and partner.vat != p_vat:
            partner.write({'vat':p_vat})
        return partner
    
    def action_approve_vote(self):
        for p in self:
            config = self.env['country.config.members'].sudo().search([('active','=',True)],limit=1)
            if not config:
                raise exceptions.UserError("No hay configuración de socios registrada por favor contacte al administrador del sistema")
            end_date_partner = fields.Date.today() + relativedelta(years=config.years_of_validity_member)
            p.write({'state_partner':'active','start_date':fields.Date.today(),'end_date_partner':end_date_partner})
            p.message_post(
                subject=_("Proceso de votación de:(%s)") % p.name,
                body=_("Proceso de votación de %s aprobada el: %s, por %s") % (
                    p.name,
                    fields.Date.today().strftime("%d/%m/%y"),
                    self.env.user.name,
                )
            )
        
    def action_suspend_partner(self):
        try:
            form_view_id = self.env.ref("Country_Socios.form_suspend_partner_wiz").id
        except Exception as e:
            form_view_id = False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Suspender: '+self.name,
            'binding_view_types': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.suspend.partner',
            'views': [(form_view_id, 'form')],
            'view_id': form_view_id,
            'target' : 'new',
            'context': {
                'default_partner_to_suspend':self.id,
            },
        }
    def action_establish_extension(self):
        try:
            form_view_id = self.env.ref("Country_Socios.form_establish_extension_wiz").id
        except Exception as e:
            form_view_id = False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Establecer Prorroga: '+self.name,
            'binding_view_types': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.establish.extension',
            'views': [(form_view_id, 'form')],
            'view_id': form_view_id,
            'target' : 'new',
            'context': {
                'default_partner_to_establish':self.id,
            },
        }

    def action_remove_suspend_partner(self):
        try:
            form_view_id = self.env.ref("Country_Socios.form_remove_suspend_partner_wiz").id
        except Exception as e:
            form_view_id = False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Remover suspension de: '+self.name,
            'binding_view_types': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.remove.suspend.partner',
            'views': [(form_view_id, 'form')],
            'view_id': form_view_id,
            'target' : 'new',
            'context': {
                'default_partner_to_remove_suspend':self.id,
            },
        }

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date:
            config = self.env['country.config.members'].sudo().search([('active','=',True)],limit=1)
            if not config:
                raise exceptions.UserError("No hay configuración de socios registrada por favor contacte al administrador del sistema")
            self.end_date_partner = self.start_date + relativedelta(years=config.years_of_validity_member)

    @api.onchange('birthday')
    def _onchange_birthday(self):
        if self.birthday:
            edad = relativedelta(datetime.now(),self.birthday)
            self.age = edad.years
            if self.type == 'contact' and self.type_relation == 'children':
                #es una carga familiar y es hijo calcular vencimiento
                config = self.env['country.config.members'].sudo().search([('active','=',True)],limit=1)
                if not config:
                    raise exceptions.UserError("No hay configuración de socios registrada por favor contacte al administrador del sistema")
                self.end_date_family = self.birthday + relativedelta(years=config.age_limit_for_associated_children)

    def name_get(self):
        res = []
        for partner in self:
            name = partner.name or ''

            if partner.company_name or partner.parent_id:
                if not name and partner.type in ['invoice', 'delivery', 'other']:
                    name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                if not partner.is_company:
                    name = "%s, %s" % (partner.commercial_company_name or partner.parent_id.name, '%s - ' % str(partner.parent_id.action_number.number) + name)
            if self._context.get('show_address_only'):
                name = partner._display_address(without_company=True)
            if self._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('show_email') and partner.email:
                name = "%s <%s>" % (name, partner.email)
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            if partner.action_number:
                name = "%s - %s" % (partner.action_number.number, name)
            res.append((partner.id, name))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        try:
            int(name)
            args = args if args else []
            args.extend([['action_number', '=', name]])
            name = ''
        except:
            pass
        return super(ResPartnerAction, self).name_search(name=name, args=args, operator=operator, limit=limit)

