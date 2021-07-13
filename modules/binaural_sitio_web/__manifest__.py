# -*- coding: utf-8 -*-
{
    'name': "binaural sitio web",

    'summary': """
       Modulo para ajustes en sitio web """,

    'description': """
        Modulo para ajustes en sitio web
    """,

    'author': "Binauraldev",
    'website': "https://binauraldev.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website/Website',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','portal','binaural_contactos_configuraciones','website_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        #'views/views.xml',
        #'views/templates.xml',
        'views/assets.xml',
        'views/portal_templates_partner.xml',
        'views/portal_templates_sale.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application':True,
}
