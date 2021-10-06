# -*- coding: utf-8 -*-
{
    'name': "Binaural_Maquina_Fiscal",

    'summary': """
        Binaural_Maquina_Fiscal""",

    'description': """
        Binaural_Maquina_Fiscal
    """,

    'author': "Binaural",
    'website': "https://binauraldev.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    
    # any module necessary for this one to work correctly
    'depends': ['base','sale','account','binaural_facturacion'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/views_payments_bin.xml',
        'views/templates.xml',
        'views/invoice_inh.xml',
        'views/sale_order_inh.xml',
        'wizard/wizard_reprint_report.xml',
        'wizard/wizard_various_report.xml',
        'views/account_tax_inh.xml',
        'views/account_journal_inh.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
