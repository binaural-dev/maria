# -*- coding: utf-8 -*-
{
    'name': "cumming inventario",

    'summary': """
        Modulo para el proceso de Inventario de la empresa cumming """,

    'description': """
        Modulo para el manejo de inventario de la empresa cumming
    """,

    'author': "Binauraldev",
    'website': "https://binauraldev.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory/Inventory',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['stock','deltatech_alternative','product_brand_inventory','product_warehouse_quantity','binaural_inventario'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/cumming_security.xml',
        'views/product_template.xml',
        'views/product_pricelist.xml',
        'views/assets.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application':True,
}
