{
    'name': 'Webapp Odoo Sync',
    'version': '1.0',
    'summary': 'Production-ready bidirectional sync with FastAPI backend for Mini Modules',
    'author': 'Arjun',
    'category': 'Integration',
    'sequence': 20,
    'depends': ['base', 'web', 'mini_sales', 'mini_inventory', 'mini_purchase', 'mini_accounting'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/sync_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
