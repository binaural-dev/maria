{
    'name': "Country_Gastos",

    'summary': """
       Personalizaciones del modulo de gastos""",

    'description': """
        Personalizaciones del modulo de gastos
    """,

    'author': "Binaural",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    "installable": True,
    "application": False,

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_expense'],

    # always loaded
    'data': [
        'views/hr_expense.xml',
        'report/hr_expense_report_inh.xml',
        'views/signature_config.xml',
        'security/ir.model.access.csv',
        'views/account_payment_inh.xml',
        ##'report/all_payment_report_inh.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
# -*- coding: utf-8 -*-
