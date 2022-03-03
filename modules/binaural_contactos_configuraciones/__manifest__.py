# -*- coding: utf-8 -*-
{
    'name': "binaural contactos configuraciones",

    'summary': """
       Modulo para información de contacto y configuraciones del sistema """,

    'description': """
        - Modelo de porcentaje de retencion
        - Modelo de tipo de persona
        - Configuración de Cuentas por defecto de IVA e ISLR para retenciones
        - Pestaña de Retenciones en contacto para informacion necesaria de las mismas
    """,

    'author': "Binauraldev",
    'website': "https://binauraldev.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Accounting',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/menuitem.xml',
        'views/views.xml',
        'views/res_partner_inh.xml',
        'views/res_config_settings_inh.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application':True,
}
