# -*- coding: utf-8 -*-
{
    'name': "Country_facturacion_campos",

    'summary': """
        Modulo para adaptar los campos de  facturacion al modelo de negocio del Country Club""",

    'description': """
        Modulo para adaptar los campos de  la facturacion al modelo de negocio del Country Club
    """,

    'author': "Binaural",
    'website': "https://binauraldev.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'Country_Socios'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/report_invoice_inh.xml',
        ##'reports/wizard_analisis_vencimiento.xml',
        'wizard/cuentas_por_cobrar_country.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
}
