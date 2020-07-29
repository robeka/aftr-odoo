from odoo import api, tools
from odoo.exceptions import UserError
from odoo.http import request
from ..product.odoo_product import MagentoSyncOdoo
from ...utils.magento.rest import Client


class Product(MagentoSyncOdoo):
    _inherit = 'product.template'

    @api.multi
    def write(self, values):
        result = super(Product, self).write(values)
        for rec in self:
            magento_backend = request.env['magento.backend'].search([], limit=1)
            if magento_backend != False:
                if rec.on_magento == True:
                    stock_quant = self.env['stock.quant'].search([('product_tmpl_id', '=', rec.id)])
                    for e in stock_quant:
                        if e.location_id.is_magento_source == True:
                            try:
                                params = {
                                    "sourceItems": [
                                        {
                                            "sku": rec.default_code,
                                            "source_code": "odoo_location_" + str(e.location_id.id),
                                            "quantity": e.quantity,
                                            "status": 1
                                        }
                                    ]
                                }
                                client = Client(magento_backend.web_url, magento_backend.access_token, True)
                                client.post('rest/V1/inventory/source-items', arguments=params)
                            except Exception as a:
                                raise UserError(
                                    ('Can not update quantity product on source magento - %s') % tools.ustr(a))
        return result
