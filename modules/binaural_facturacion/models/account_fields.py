from odoo import api, fields, models
from lxml import etree
import json
import logging

_logger = logging.getLogger(__name__)
class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        foreign_currency_id = self.env["ir.config_parameter"].sudo().get_param("curreny_foreign_id")
        municipality_retention = self.env["ir.config_parameter"].sudo(
        ).get_param("use_municipal_retention")
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
        if not municipality_retention and view_type == "form":
            doc = etree.XML(res["arch"])
            municipality_field = doc.xpath(
                "//field[@name='municipality_tax']")[0]
            modifiers_field = json.loads(municipality_field.get("modifiers") or '{}')
            modifiers_field['invisible'] = True
            municipality_field.set('modifiers', json.dumps(modifiers_field))
            
            municipality_voucher = doc.xpath(
                "//field[@name='municipality_tax_voucher']")[0]
            modifiers_voucher = json.loads(municipality_voucher.get("modifiers") or '{}')
            modifiers_voucher['invisible'] = True
            municipality_voucher.set('modifiers', json.dumps(modifiers_voucher))
            res["arch"] = etree.tostring(doc, encoding="unicode")
            
        elif municipality_retention and view_type == 'form':
            context = dict(self._context or {})
            
            # _logger.warning("context: %s", context)
            # record = self.env['account.move'].browse(context['default_move_type']['id'] or None)
            
            if context['default_move_type'] in ['in_invoice', 'in_refund']:
                doc = etree.XML(res["arch"])
                municipality_field = doc.xpath(
                    "//field[@name='municipality_tax']")[0]
                modifiers_field = json.loads(municipality_field.get("modifiers") or '{}')
                modifiers_field['invisible'] = False
                municipality_field.set('modifiers', json.dumps(modifiers_field))
                
                municipality_voucher = doc.xpath(
                    "//field[@name='municipality_tax_voucher']")[0]
                modifiers_voucher = json.loads(municipality_voucher.get("modifiers") or '{}')
                modifiers_voucher['invisible'] = False
                municipality_voucher.set('modifiers', json.dumps(modifiers_voucher))
                res["arch"] = etree.tostring(doc, encoding="unicode")
            else:
                doc = etree.XML(res["arch"])
                municipality_field = doc.xpath(
                    "//field[@name='municipality_tax']")[0]
                modifiers_field = json.loads(municipality_field.get("modifiers") or '{}')
                modifiers_field['invisible'] = True
                municipality_field.set('modifiers', json.dumps(modifiers_field))
                
                municipality_voucher = doc.xpath(
                    "//field[@name='municipality_tax_voucher']")[0]
                modifiers_voucher = json.loads(municipality_voucher.get("modifiers") or '{}')
                modifiers_voucher['invisible'] = True
                municipality_voucher.set('modifiers', json.dumps(modifiers_voucher))
                res["arch"] = etree.tostring(doc, encoding="unicode")
            
        return res


class AccountRetention(models.Model):
    _inherit = "account.retention"

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        # foreign_currency_id = self.env["ir.config_parameter"].sudo().get_param("curreny_foreign_id")
        if view_type == "form":
            doc = etree.XML(res["fields"]["retention_line"]["views"]["tree"]["arch"])
            facture_amount = doc.xpath("//field[@name='facture_amount']")[0]
            facture_amount.set("string", "Base Imponible Bs.F")
            facture_total = doc.xpath("//field[@name='facture_total']")[0]
            facture_total.set("string", "Total Factura Bs.F")
            iva_amount = doc.xpath("//field[@name='iva_amount']")[0]
            iva_amount.set("string", "Iva Factura Bs.F")
            retention_amount = doc.xpath("//field[@name='retention_amount']")[0]
            retention_amount.set("string", "Monto Retenido Bs.F")


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
