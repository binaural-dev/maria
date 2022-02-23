from odoo import api, fields, models
from lxml import etree


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        foreign_currency_id = self.env["ir.config_parameter"].sudo().get_param("curreny_foreign_id")
        if foreign_currency_id and foreign_currency_id == '2':
            if view_type == "tree":
                doc = etree.XML(res["arch"])
                foreign_amount_total = doc.xpath("//field[@name='foreign_amount_total']")
                if foreign_amount_total:
                    foreign_amount_total[0].set("string", "Total Moneda $")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
            elif view_type == "form":
                doc = etree.XML(res["fields"]["invoice_line_ids"]["views"]["tree"]["arch"])
                foreign_price_unit = doc.xpath("//field[@name='foreign_price_unit']")[0]
                foreign_price_unit.set("string", "Precio $")
                foreign_subtotal = doc.xpath("//field[@name='foreign_subtotal']")[0]
                foreign_subtotal.set("string", "Subtotal $")
                res["fields"]["invoice_line_ids"]["views"]["tree"]["arch"] = etree.tostring(doc, encoding="unicode")

                doc = etree.XML(res["fields"]["retention_iva_line_ids"]["views"]["tree"]["arch"])
                foreign_facture_amount = doc.xpath("//field[@name='foreign_facture_amount']")[0]
                foreign_facture_amount.set("string", "Base Imponible $")
                foreign_facture_total = doc.xpath("//field[@name='foreign_facture_total']")[0]
                foreign_facture_total.set("string", "Total Factura $")
                foreign_iva_amount = doc.xpath("//field[@name='foreign_iva_amount']")[0]
                foreign_iva_amount.set("string", "Iva Factura $")
                foreign_retention_amount = doc.xpath("//field[@name='foreign_retention_amount']")[0]
                foreign_retention_amount.set("string", "Monto Retenido $")
                res["fields"]["retention_iva_line_ids"]["views"]["tree"]["arch"] = etree.tostring(doc, encoding="unicode")

                doc = etree.XML(res["fields"]["retention_islr_line_ids"]["views"]["tree"]["arch"])
                foreign_facture_amount = doc.xpath("//field[@name='foreign_facture_amount']")[0]
                foreign_facture_amount.set("string", "Base Imponible $")
                foreign_facture_total = doc.xpath("//field[@name='foreign_facture_total']")[0]
                foreign_facture_total.set("string", "Total Factura $")
                foreign_iva_amount = doc.xpath("//field[@name='foreign_iva_amount']")[0]
                foreign_iva_amount.set("string", "Iva Factura $")
                foreign_retention_amount = doc.xpath("//field[@name='foreign_retention_amount']")[0]
                foreign_retention_amount.set("string", "Monto Retenido $")
                res["fields"]["retention_islr_line_ids"]["views"]["tree"]["arch"] = etree.tostring(doc, encoding="unicode")
        elif foreign_currency_id and foreign_currency_id == '3':
            if view_type == "tree":
                doc = etree.XML(res["arch"])
                foreign_amount_total = doc.xpath("//field[@name='foreign_amount_total']")
                if foreign_amount_total:
                    foreign_amount_total[0].set("string", "Total Moneda Bs.F")
                    res["arch"] = etree.tostring(doc, encoding="unicode")
            elif view_type == "form":
                doc = etree.XML(res["fields"]["invoice_line_ids"]["views"]["tree"]["arch"])
                foreign_price_unit = doc.xpath("//field[@name='foreign_price_unit']")[0]
                foreign_price_unit.set("string", "Precio Bs.F")
                foreign_subtotal = doc.xpath("//field[@name='foreign_subtotal']")[0]
                foreign_subtotal.set("string", "Subtotal Bs.F")
                res["fields"]["invoice_line_ids"]["views"]["tree"]["arch"] = etree.tostring(doc, encoding="unicode")

                doc = etree.XML(res["fields"]["retention_iva_line_ids"]["views"]["tree"]["arch"])
                foreign_facture_amount = doc.xpath("//field[@name='foreign_facture_amount']")[0]
                foreign_facture_amount.set("string", "Base Imponible Bs.F")
                foreign_facture_total = doc.xpath("//field[@name='foreign_facture_total']")[0]
                foreign_facture_total.set("string", "Total Factura Bs.F")
                foreign_iva_amount = doc.xpath("//field[@name='foreign_iva_amount']")[0]
                foreign_iva_amount.set("string", "Iva Factura Bs.F")
                foreign_retention_amount = doc.xpath("//field[@name='foreign_retention_amount']")[0]
                foreign_retention_amount.set("string", "Monto Retenido Bs.F")
                res["fields"]["retention_iva_line_ids"]["views"]["tree"]["arch"] = etree.tostring(doc, encoding="unicode")

                doc = etree.XML(res["fields"]["retention_islr_line_ids"]["views"]["tree"]["arch"])
                foreign_facture_amount = doc.xpath("//field[@name='foreign_facture_amount']")[0]
                foreign_facture_amount.set("string", "Base Imponible Bs.F")
                foreign_facture_total = doc.xpath("//field[@name='foreign_facture_total']")[0]
                foreign_facture_total.set("string", "Total Factura Bs.F")
                foreign_iva_amount = doc.xpath("//field[@name='foreign_iva_amount']")[0]
                foreign_iva_amount.set("string", "Iva Factura Bs.F")
                foreign_retention_amount = doc.xpath("//field[@name='foreign_retention_amount']")[0]
                foreign_retention_amount.set("string", "Monto Retenido Bs.F")
                res["fields"]["retention_islr_line_ids"]["views"]["tree"]["arch"] = etree.tostring(doc, encoding="unicode")
        return res


class AccountRetention(models.Model):
    _inherit = "account.retention"

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        foreign_currency_id = self.env["ir.config_parameter"].sudo().get_param("curreny_foreign_id")
        if foreign_currency_id and foreign_currency_id == '2':
            if view_type == "form":
                doc = etree.XML(res["fields"]["retention_line"]["views"]["tree"]["arch"])
                foreign_facture_amount = doc.xpath("//field[@name='foreign_facture_amount']")[0]
                foreign_facture_amount.set("string", "Base Imponible $")
                foreign_facture_total = doc.xpath("//field[@name='foreign_facture_total']")[0]
                foreign_facture_total.set("string", "Total Factura $")
                foreign_iva_amount = doc.xpath("//field[@name='foreign_iva_amount']")[0]
                foreign_iva_amount.set("string", "Iva Factura $")
                foreign_retention_amount = doc.xpath("//field[@name='foreign_retention_amount']")[0]
                foreign_retention_amount.set("string", "Monto Retenido $")
                res["fields"]["retention_line"]["views"]["tree"]["arch"] = etree.tostring(doc, encoding="unicode")
        elif foreign_currency_id and foreign_currency_id == '3':
            if view_type == "form":
                doc = etree.XML(res["fields"]["retention_line"]["views"]["tree"]["arch"])
                foreign_facture_amount = doc.xpath("//field[@name='foreign_facture_amount']")[0]
                foreign_facture_amount.set("string", "Base Imponible Bs.F")
                foreign_facture_total = doc.xpath("//field[@name='foreign_facture_total']")[0]
                foreign_facture_total.set("string", "Total Factura Bs.F")
                foreign_iva_amount = doc.xpath("//field[@name='foreign_iva_amount']")[0]
                foreign_iva_amount.set("string", "Iva Factura Bs.F")
                foreign_retention_amount = doc.xpath("//field[@name='foreign_retention_amount']")[0]
                foreign_retention_amount.set("string", "Monto Retenido Bs.F")
                res["fields"]["retention_line"]["views"]["tree"]["arch"] = etree.tostring(doc, encoding="unicode")
        return res
