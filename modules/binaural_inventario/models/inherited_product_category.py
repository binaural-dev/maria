from odoo import models, fields, api
from lxml import etree
import json

class InheritedProductCategoryImpuestos(models.Model):
    _inherit = 'product.category'
    
    ciu = fields.Many2one('economic.activity',string='CIU') 
    
    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id,
                                      view_type=view_type, toolbar=toolbar, submenu=submenu)
        municipality_retention = self.env["ir.config_parameter"].sudo(
        ).get_param("use_municipal_retention")
        if not municipality_retention and view_type == "form":
            doc = etree.XML(res["arch"])
            municipality_field = doc.xpath(
                "//field[@name='ciu']")[0]
            modifiers = json.loads(municipality_field.get("modifiers"))
            modifiers['invisible'] = True
            municipality_field.set('modifiers', json.dumps(modifiers))
            res["arch"] = etree.tostring(doc, encoding="unicode")
        return res