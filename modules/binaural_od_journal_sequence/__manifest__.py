# -*- coding: utf-8 -*-
{
    'name': "binaural Ajustes oj_journal_sequence",

    'summary': """
       Modulo para corregir secuencia de facturas de proveedor """,

    'description': """
        Modulo para corregir secuencia de facturas de proveedor
    """,

    'author': "Binauraldev",
    'website': "https://binauraldev.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': '',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['od_journal_sequence'],

    'data': [
        'views/account_move.xml',
    ],
    'demo': [
    ],
    'application':True,
}
