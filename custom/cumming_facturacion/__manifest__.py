# -*- coding: utf-8 -*-
{
    'name': "cumming facturacion",

    'summary': """
        Modulo para el proceso de facturacion de la empresa cumming """,

    'description': """
        Modulo para el manejo de facturacion de la empresa cumming
    """,

    'author': "Binauraldev",
    'website': "https://binauraldev.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Accounting',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['account','binaural_facturacion'],

    # always loaded
    'data': [
        #'data/formato_papel.xml',
        #'report/report_invoice_document_override.xml',
        'report/invoice_free_form.xml',
        'report/invoice_free_form_bs.xml',
        'views/res_partner.xml',
        'views/account_move.xml',
        'views/sale_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application':True,
}
