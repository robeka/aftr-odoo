# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "UPS Shipping Integration",
  "summary"              :  "The module allows the user to Integrate United Postal Services, UPS with Odoo. Once integrated, the shipping method can be used on Odoo website by customers to get their orders delivered and in the Odoo backend by the user.",
  "category"             :  "Website",
  "version"              :  "1.0.11",
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "maintainer"           :  "Aditya Sharma",
  "website"              :  "https://store.webkul.com/Odoo-Website-UPS-Shipping-Integration.html",
  "description"          :  """United Parcel Services
Odoo UPS Shipping Integration
Deliver orders Odoo
UPS shipping
Ship orders
Odoo parcel delivery
Parcel shipping
National delivery
International shipping
Domestic shipping
Domestic delivery
Shipping prices Odoo
UPS integration Odoo
Odoo UPS
UPS integrate
Use UPS
UPS shipping carrier
UPS delivery Odoo
Odoo Shipping integration
Integration shipping carrier in Odoo
Odoo delivery integration
Odoo delivery methods
Delivery carrier tracking
Shipping modules odoo
Deliveries
Manage order delivery
shipping methods odoo""",
  "live_test_url"        :  "https://webkul.com/blog/odoo-website-ups-shipping-integration/",
  "depends"              :  ['odoo_shipping_service_apps'],
  "data"                 :  [
                             'views/ups_delivery_carrier.xml',
                             'views/product_packaging.xml',
                             'security/ir.model.access.csv',
                             'data/data.xml',
                             'data/delivery_demo.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "price"                :  149,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
  "external_dependencies":  {'python': ['urllib3']},
}