{
    'name': "Country_Socios",

    'summary': """
       Acciones y socios""",

    'description': """
        Acciones y socios
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
    'depends': ['base', 'account', 'binaural_contactos_configuraciones'],
    ##gregar dependencia de cxc
    ###gregar dependencia de accounting_reports
    # always loaded
    'data': [
		'security/ir.model.access.csv',
        'views/action_partner.xml',
		'views/res_partner.xml',
		'views/account_invoice.xml',
		'views/account_payment.xml',
		##'reports/sale_book.xml',
        'wizard/status_batch.xml',
        'wizard/action_batch.xml',
        ##'views/account_cxc_inh.xml',
        'views/assets.xml',
        'views/professions.xml',
        'views/associate_list.xml',
        'views/members_config.xml',
        ##'reports/shopping_book.xml',
        'wizard/suspend_partner.xml',
        'data/cron.xml',
        'wizard/establish_extension.xml',
        'data/email_template_alert_end_date.xml',
        'views/partner_insolvent.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
# -*- coding: utf-8 -*-
