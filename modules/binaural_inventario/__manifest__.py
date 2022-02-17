# -*- coding: utf-8 -*-
{
    'name': "binaural inventario",

    'summary': """
        Modulo para el proceso de Inventario """,

    'description': """
        Modulo para el manejo de multimonedas
    """,

    'author': "Binauraldev",
    'website': "https://binauraldev.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory/Inventory',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'binaural_contactos_configuraciones', 'sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/security.xml',
        'views/res_config.xml',
        'views/stock_picking.xml',
        'views/product_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application':True,
}
