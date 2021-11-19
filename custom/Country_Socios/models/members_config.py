# -*- coding: utf-8 -*-
import hashlib
import hmac
import logging
import lxml
import random
import re
import threading
from ast import literal_eval
from base64 import b64encode

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo import models, fields, api, exceptions, _
image_re = re.compile(r"data:(image/[A-Za-z]+);base64,(.*)")
EMAIL_PATTERN = '([^ ,;<@]+@[^> ,;]+)'


class ConfigMembers(models.Model):
	_name = 'country.config.members'
	_rec_name = "company_id"

	def get_company_def(self):
		return self.env.user.company_id
	
	company_id = fields.Many2one('res.company', default=get_company_def, string='Compañía', readonly=True)
	active = fields.Boolean(default=True, string="Activo")
	years_of_validity_member = fields.Integer(string="Años de vigencia del socio",required=True)
	age_limit_for_associated_children = fields.Integer(string="Edad límite para hijos asociados",required=True)
	previous_days_alert_associates = fields.Integer(string="Días anteriores para alerta de vigencia de asociación para asociados familiares",required=True)
	
	out_email_alert_associates = fields.Char(string='Correo de salida para alerta de asociados')#preguntar si es el mosimo subject de los demas

	expiration_alert_subject = fields.Char(string="Asunto de correo de alerta de vencimiento")
	expiration_alert_body = fields.Html(string="Cuerpo de correo de alerta de vencimiento",sanitize_attributes=False)

	
	extension_alert_subject = fields.Char(string="Asunto de correo de alerta de prórroga")
	extension_alert_body = fields.Html(string="Cuerpo de correo de alerta de prórroga",sanitize_attributes=False)


	signature  = fields.Binary(string='Firma')

	@api.onchange('out_email_alert_associates')
	def _compute_is_email_valid(self):
		for record in self:
			if record.out_email_alert_associates:
				is_email_valid = re.match(EMAIL_PATTERN, record.out_email_alert_associates)
				if not is_email_valid:
					raise UserError("Correo invalido")

	@api.model
	def create(self, values):
		if values.get('expiration_alert_body'):
			values['expiration_alert_body'] = self._convert_inline_images_to_urls(values['expiration_alert_body'])
		if values.get('extension_alert_body'):
			values['extension_alert_body'] = self._convert_inline_images_to_urls(values['extension_alert_body'])
		return super(ConfigMembers, self).create(values)

	def write(self, values):
		if values.get('expiration_alert_body'):
			values['expiration_alert_body'] = self._convert_inline_images_to_urls(values['expiration_alert_body'])
		if values.get('extension_alert_body'):
			values['extension_alert_body'] = self._convert_inline_images_to_urls(values['extension_alert_body'])

		return super(ConfigMembers, self).write(values)
	
	def _convert_inline_images_to_urls(self, body_html):
		"""
		Find inline base64 encoded images, make an attachement out of
		them and replace the inline image with an url to the attachement.
		"""

		def _image_to_url(b64image: bytes):
			"""Store an image in an attachement and returns an url"""
			attachment = self.env['ir.attachment'].create({
				'name': "cropped_image",
				'datas': b64image,
				'datas_fname': "cropped_image_mailing_{}".format(self.id),
				'type': 'binary',})

			attachment.generate_access_token()

			return '/web/image/%s?access_token=%s' % (
				attachment.id, attachment.access_token)


		modified = False
		root = lxml.html.fromstring(body_html)
		for node in root.iter('img'):
			match = image_re.match(node.attrib.get('src', ''))
			if match:
				mime = match.group(1)  # unsed
				image = match.group(2).encode()  # base64 image as bytes

				node.attrib['src'] = _image_to_url(image)
				modified = True

		if modified:
			return lxml.html.tostring(root)

		return body_html