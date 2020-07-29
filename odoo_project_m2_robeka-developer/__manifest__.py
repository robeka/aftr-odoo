# -*- coding: utf-8 -*-
{
    'name': "odoo_magento_integration",

    'summary': """
       Made by Magenest""",

    'description': """
        Real-time automatic synchronization of products and warehouses details between Magento and Odoo
    """,

    'author': "Magenest",
    'website': "http://www.yourcompany.com",
    'category': 'Magento Connector',
    'version': '0.1',
    'depends': ['base', 'account', 'sale', 'sale_management', 'product', 'payment', 'stock', 'sale_stock', 'delivery', ],
    'data': [
        'security/ir.model.access.csv',
        # 'demo/payment_method_data.xml',
        'views/menu.xml',
        'views/config/magento_instance.xml',
        'views/partner/res_partner.xml',
        'views/dashboard/website.xml',
        'views/dashboard/store.xml',
        'views/dashboard/storeview.xml',
        'views/dashboard/dashboard_view.xml',
        'views/stock/stock_production_lot_view.xml',
        # 'views/stock_location/stock_delivery_method.xml',
        # 'views/stock_location/stock_location_view.xml',
        # 'views/product/product_template_sync.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
