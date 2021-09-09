# -*- coding: utf-8 -*-
{
    'name': "Binaural Reporte Fiscal",

    'summary': """
       Modulo para los reportes fiscales """,

    'description': """
        
    """,

    'author': "Binauraldev",
    'website': "https://binauraldev.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Accounting',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['binaural_facturacion'],

    # always loaded
    'data': [
        'data/paperformat.xml',
        'data/sequence_arcv.xml',
        'security/ir.model.access.csv',
        'report/template_retention_iva_voucher.xml',
        'report/retention_iva_voucher.xml',
        'report/report_arcv.xml',
        'views/account_retention.xml',
        'views/mail_template.xml',
        'wizard/txt_wizard.xml',
        'wizard/arcv_wizard.xml',
    ],
    'external_dependencies': {
       'python': ['pandas'],
    },
    # only loaded in demonstration mode
    'demo': [],
    'application': False,
}
