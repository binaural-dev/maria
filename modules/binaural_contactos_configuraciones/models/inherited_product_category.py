from odoo import models, fields, api


class InheritedProductCategoryImpuestos(models.Model):
    _inherit = 'product.category'
    
    ciu = fields.Char(string='CIU') 