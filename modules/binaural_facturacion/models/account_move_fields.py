from odoo import api, fields, models
from lxml import etree


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        foreign_currency_id = self.env["ir.config_parameter"].sudo().get_param("curreny_foreign_id")
        if foreign_currency_id and foreign_currency_id == '2':
            doc = etree.XML(res["arch"])
            if view_type == "tree":
                foreign_amount_total = doc.xpath("//field[@name='foreign_amount_total']")
                if foreign_amount_total:
                    foreign_amount_total[0].set("string", "Total Moneda $")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
        elif foreign_currency_id and foreign_currency_id == '3':
            doc = etree.XML(res["arch"])
            if view_type == "tree":
                foreign_amount_total = doc.xpath("//field[@name='foreign_amount_total']")
                if foreign_amount_total:
                    foreign_amount_total[0].set("string", "Total Moneda Bs.F")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
        return res
