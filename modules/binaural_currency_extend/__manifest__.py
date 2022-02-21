# -*- coding: utf-8 -*-
{
    'name': "binaural Calculos Moneda",

    'author': "Binauraldev",
    'website': "https://binauraldev.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'data/decimal_precision.xml',
        'views/views.xml',
    ],
    'application':True,
}
