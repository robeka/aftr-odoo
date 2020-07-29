from odoo import models, tools
from odoo.exceptions import UserError
from odoo.http import request
from ...utils.magento.rest import Client


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def action_validate(self):
        super(StockInventory, self).action_validate()
        magento_backend = request.env['magento.backend'].search([], limit=1)
        for e in self.line_ids:
            if e.location_id.usage == 'internal' and e.location_id.is_magento_source and e.product_id.on_magento == True:
                try:
                    params = {
                        "sourceItems": [
                            {
                                "sku": e.product_id.default_code,
                                "source_code": "odoo_location_" + str(e.location_id.id),
                                "quantity": e.product_qty,
                                "status": 1
                            }
                        ]
                    }
                    client = Client(magento_backend.web_url, magento_backend.access_token, True)
                    client.post('rest/V1/inventory/source-items', arguments=params)
                except Exception as a:
                    raise UserError(('Can not update quantity product on source magento - %s') % tools.ustr(a))
