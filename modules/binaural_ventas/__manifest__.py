# -*- coding: utf-8 -*-
{
    'name': "binaural ventas",

    'summary': """
       Modulo para el proceso de Ventas """,

    'description': """
        Modulo para el proceso de Ventas con manejo de multimonedas
    """,

    'author': "Binauraldev",
    'website': "https://binauraldev.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales/Sales',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','sale_management','binaural_contactos_configuraciones'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        #'views/views.xml',
        #'views/templates.xml',
        'views/res_config.xml',
        'views/sale_form_inh.xml',
        'views/sale_search_inh.xml',
        'views/sale_trees_inh.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application':True,
}
