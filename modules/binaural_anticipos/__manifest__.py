# -*- coding: utf-8 -*-
{
    'name': "Binaural_Anticipo_Proveedores/Clientes",

    'summary': """
        Binaural Anticipo Proveedores/Clientes
        Registrar pagos anticipados de clientes y proveedores y asociarlos en caso de ser necesario a las facturas.""",

    'description': """
        Binaural Anticipo Proveedores/Clientes
        Registrar pagos anticipados de clientes y proveedores y asociarlos en caso de ser necesario a las facturas.
    """,

    'author': "Binaural",
    'website': "https://binauraldev.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account', 'account_accountant', 'binaural_facturacion'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/account_payment_inh.xml',
        'views/account_advance_config.xml',
        'wizard/wizard_payment_report.xml',
        'wizard/advance_payment_report.xml',
        'reports/all_payment_report.xml',
        'reports/report_advance_payment_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}