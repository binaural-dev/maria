"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import re
import ast
import functools
import json
import logging
from odoo.exceptions import AccessError

from odoo import http
from odoo.addons.yacambu_restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
)
from odoo.http import request

_logger = logging.getLogger(__name__)


def validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)
        access_token_data = (
            request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
        )

        if access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response("access_token", "token seems to have expired or invalid", 401)

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap


_routes = ["/api/<model>", "/api/<model>/<id>", "/api/<model>/<id>/<action>"]


class APIController(http.Controller):
    """."""

    def __init__(self):
        self._model = "ir.model"

    @validate_token
    @http.route(_routes, type="json", auth="none", methods=["GET"], csrf=False)
    def get(self, model=None, id=None, **payload):
        try:
            ioc_name = model
            model = request.env[self._model].search([("model", "=", model)], limit=1)
            if model:
                domain, fields, offset, limit, order = extract_arguments(payload)
                data = request.env[model.model].search_read(
                    domain=domain, fields=fields, offset=offset, limit=limit, order=order,
                )
                if id:
                    domain = [("id", "=", int(id))]
                    data = request.env[model.model].search_read(
                        domain=domain, fields=fields, offset=offset, limit=limit, order=order,
                    )
            if data:
                return {'status': 200, 'msg': "CORRECTO", "data":data}
                  
            else:
                return invalid_response(
                    "invalid object model", "The model %s is not available in the registry." % ioc_name,
                )
        except AccessError as e:

            return invalid_response("Access error", "Error: %s" % e.name)

    @validate_token
    @http.route(_routes, type="json", auth="none", methods=["POST"], csrf=False)
    def post(self, model=None, id=None, **payload ):
        import ast
        _logger.info("PAYLOAD 1 %s", payload)
        #-----------------------descomentar antes de subir
        # payload = payload.get("payload", {})
        #pendiente de manera producto por codigo y no id
        ioc_name = model
        model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        values = {}
        variable = {}
        if model:
            try:
                _logger.info("PAYLOAD 2 %s",payload)
                # changing IDs from string to int.
                for k, v in payload.items():
                    if "__api__" in k:
                        _logger.info("hola %s",k)
                        values[k[7:]] = ast.literal_eval(v)
                    else:
                        _logger.info("PARSEAR %s",v)
                        _logger.info("TYPE OF %s",type(v))
                        values[k] = ast.literal_eval(str(v))
                    # balance_item.invoice_id.partner_id
                if model.model == 'account.payment':
                    _logger.info("HOLIS ESTA ES UN PAGO DE FACTURA")
                    try:
                        _id = int(id)
                        _logger.info("id 1 %s", _id)
                    except Exception as e:
                        return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
                    try:
                        resource = request.env[model.model].sudo().create(values) #creo el pago
                        resource.sudo().action_post() #posteo
                        payment = request.env[model.model].sudo().search_read([("id", '=', int(resource.id))]) #busco el pago
                        record = request.env['account.move'].sudo().search_read([("id", "=", _id)]) #busco la factura a pagar
                        if record and resource:
                            move_id = payment[0].get('move_id') #obtengo el move_id
                            invoice_id = record[0].get('id') #obtengo invoice_id
                            partner_id = record[0].get('partner_id') #obtengo partner_id
                            
                            if invoice_id and partner_id and move_id:
                                partial = request.env['account.payment'].sudo().paymnt_invoices(partner_id[0],invoice_id,move_id[0])
                                data = resource.sudo().read()
                                _logger.info("daata %s", data)
                                return {'status': 200, 'msg': "CORRECTO","id":resource.id, "data":data}          
                        else:
                            return invalid_response("missing_record", "record object with id %s could not be found" % _id, 404,)
                    except Exception as e:
                        return invalid_response("exception", e)  

                else:
                    _logger.info("PAYLOAS5 %s",payload)
                    _logger.info("VALORES %s",values)
                    _logger.info("model.model %s",model.model)
                    resource = request.env[model.model].sudo().create(values)
                    _logger.info("RESOURCE %s",resource)
                
            except Exception as e:
                request.env.cr.rollback()
                _logger.info("EXEPT %s",e)
                return invalid_response("params", e)
            else:
                data = resource.sudo().read()
                if resource:
                    return {'status': 200, 'msg': "CORRECTO","id":resource.id, "data":data}
                    #return valid_response(data)
                else:
                    return {'status': 200, 'msg': "CORRECTO"}
                    #return valid_response(data)
        return invalid_response("invalid object model", "The model %s is not available in the registry." % ioc_name,)

    @validate_token
    @http.route(_routes, type="json", auth="none", methods=["PUT"], csrf=False)
    def put(self, model=None, id=None, **payload):
        """."""
        #payload = payload.get('payload', {})
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        _model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        values = {}
        if not _model:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model, 404,
            )
        try:
            record = request.env[_model.model].sudo().browse(_id)
            for k, v in payload.items():
                if "__api__" in k:
                    values[k[7:]] = ast.literal_eval(v)
                else:
                    _logger.info("PARSEAR %s",v)
                    values[k] = ast.literal_eval(v)
            record.write(values)
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("exception", e)
        else:
            data = record.sudo().read()
            return {'status': 200, 'msg': "CORRECTO", 'data': data}
            #return valid_response(record.read())

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["DELETE"], csrf=False)
    def delete(self, model=None, id=None, **payload):
        """."""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        try:
            record = request.env[model].sudo().search([("id", "=", _id)])
            if record:
                record.unlink()
            else:
                return invalid_response("missing_record", "record object with id %s could not be found" % _id, 404,)
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("exception", e.name, 503)
        else:
            return valid_response("record %s has been successfully deleted" % record.id)

    @validate_token
    @http.route(_routes, type="json", auth="none", methods=["PATCH"], csrf=False)
    def patch(self, model=None, id=None, action=None, **payload):
        """."""
        #payload = payload.get('payload')
        if action:
            action = action 
        else:
             if payload.get("_method"):
                action = payload.get("_method")
        args = []
        _logger.info("action 1 %s", action)
        try:
            _id = int(id)
            _logger.info("id 1 %s", _id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base" % id)
        try:
            record = request.env[model].sudo().search([("id", "=", _id)])
            _logger.info("record 1 %s", record)
            _callable = action in [method for method in dir(record) if callable(getattr(record, method))]
            _logger.info("callable 1 %s", _callable)
            if record and _callable:
                # action is a dynamic variable.
                getattr(record, action)(*args) if args else getattr(record, action)() 
            else:
                return invalid_response(
                    "missing_record",
                    "record object with id %s could not be found or %s object has no method %s" % (_id, model, action),
                    404,
                )
        except Exception as e:
            return invalid_response("exception", e, 503)
        else:
             return {'status': 200, 'msg': "CORRECTO", 'id': record.id}

