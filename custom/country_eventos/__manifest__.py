{
    'name': "country_eventos",

    'summary': """
       Binaural eventos invitaciones""",

    'description': """
        Binaural eventos invitaciones
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
    'depends': ['base', 'event', 'website_event', 'website_event_sale'],

    # always loaded
    'data': [
        'views/configurate_qty_entries.xml',
        'views/event.xml',
        'reports/event_template.xml',
        'reports/report_event.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
# -*- coding: utf-8 -*-
