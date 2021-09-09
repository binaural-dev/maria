# -*- coding: utf-8 -*-
from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools import config, float_compare


class StockQuantBinauralInventario(models.Model):
    _inherit = "stock.quant"

    @api.constrains("product_id", "quantity")
    def check_negative_qty_binaural_inventario(self):
        p = self.env["decimal.precision"].precision_get("Product Unit of Measure")

        for quant in self:
            #disallowed_by_product = (
            #    not quant.product_id.allow_negative_stock
            #    and not quant.product_id.categ_id.allow_negative_stock
            #)
            #disallowed_by_location = not quant.location_id.allow_negative_stock
            disallowed = self.env['ir.config_parameter'].sudo().get_param('not_qty_on_hand_less_zero')
            if (
                float_compare(quant.quantity, 0, precision_digits=p) == -1
                and quant.product_id.type == "product"
                and quant.location_id.usage in ["internal", "transit"]
                and disallowed
            ):
                msg_add = ""
                if quant.lot_id:
                    msg_add = _(" lot '%s'") % quant.lot_id.name_get()[0][1]
                raise ValidationError(
                    _(
                        "No se puede validar esta operación de stock porque el nivel de stock del "
                        "producto '%s'%s se volvería negativo (%s) en la ubicación de stock '%s' y no "
                        "se permite stock negativo."
                    )
                    % (
                        quant.product_id.name,
                        msg_add,
                        quant.quantity,
                        quant.location_id.complete_name,
                    )
                )
