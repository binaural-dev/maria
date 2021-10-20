# -*- coding: utf-8 -*-
{
    'name': "Country_Facturas_Lote",

    'summary': """
        Crear facturas según estatus de socios y productos""",

    'description': """
        Crear facturas según estatus de socios y productos
    """,

    'author': "Binaural",
    'website': "www.binauraldev.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','Country_Socios','product'],

    # always loaded
    'data': [
         'security/ir.model.access.csv',
        'views/product_inh.xml',
        'wizard/invoice_batch.xml',
        'security/ir.model.access.csv',
        'views/config_journal_batch_config.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
