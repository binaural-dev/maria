# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2021-Today Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################
from odoo.tools import pycompat,float_is_zero
from odoo.tools.float_utils import float_round
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
class ProductTemplate(models.Model):
    _inherit = "product.template"

    warehouse_quantity = fields.Char(compute='_get_warehouse_quantity', string='Cantidad por almacén')

    quantity_csa = fields.Char(compute='_get_warehouse_quantity', string='Cantidad en CSA')
    quantity_repubus = fields.Char(compute='_get_warehouse_quantity', string='Cantidad en CSA 2')

    def button_dummy_ware(self):
        pass

    def button_dummy_ware_2(self):
        pass

    def _get_warehouse_quantity(self):
        for record in self:
            warehouse_quantity_text = ''
            record.quantity_csa = 0
            record.quantity_repubus = 0
            product_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=', record.id)])
            if product_id:
                quant_ids = self.env['stock.quant'].sudo().search([('product_id','=',product_id[0].id),('location_id.usage','=','internal')])
                t_warehouses = {}
                rounding = product_id.uom_id.rounding
                for quant in quant_ids:
                    if quant.location_id:
                        if quant.location_id not in t_warehouses:
                            t_warehouses.update({quant.location_id:0})
                        t_warehouses[quant.location_id] += float_round(quant.quantity - quant.reserved_quantity,precision_rounding=rounding)

                tt_warehouses = {}
                for location in t_warehouses:
                    warehouse = False
                    location1 = location
                    while (not warehouse and location1):
                        warehouse_id = self.env['stock.warehouse'].sudo().search([('lot_stock_id','=',location1.id)])
                        if len(warehouse_id) > 0:
                            warehouse = True
                        else:
                            warehouse = False
                        location1 = location1.location_id
                    if warehouse_id:
                        if warehouse_id.code not in tt_warehouses:
                            tt_warehouses.update({warehouse_id.code:0})
                        tt_warehouses[warehouse_id.code] += t_warehouses[location]

                for item in tt_warehouses:
                    if tt_warehouses[item] != 0:
                        warehouse_quantity_text = warehouse_quantity_text + ' ** ' + item + ': ' + str(tt_warehouses[item])
                record.warehouse_quantity = warehouse_quantity_text
                _logger.info(tt_warehouses)
   
                cont = 0
                for item in tt_warehouses:
                    if cont == 0:
                        if tt_warehouses[item]:
                            record.quantity_csa = item + ': ' + str(tt_warehouses[item])
                    if cont == 1:
                        if tt_warehouses[item]:
                            record.quantity_repubus = item + ': ' + str(tt_warehouses[item])

                    cont+=1
