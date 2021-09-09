# -*- coding: utf-8 -*-
{
    'name': "binaural gastos",

    'summary': """
       Modulo para el proceso de Gastos """,

    'description': """
        Modulo para el proceso de Gastos
    """,

    'author': "Binauraldev",
    'website': "https://binauraldev.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': '',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_expense', 'binaural_contactos_configuraciones', 'binaural_facturacion'],

    'data': [
        'views/hr_expense.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application':True,
}
