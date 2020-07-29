from odoo import models, fields, api, tools
from odoo.exceptions import UserError, Warning
from odoo.http import request
from ...utils.magento.rest import Client


class StockLocation(models.Model):
    _inherit = 'stock.location'

    country_id = fields.Many2one('res.country', string='Country')
    post_code = fields.Char(string='Post Code')
    is_magento_source = fields.Boolean(string='Is Magento Source')

    @api.model
    def create(self, vals):
        stock_location = super(StockLocation, self).create(vals)
        magento_backend = request.env['magento.backend'].search([], limit=1)

        if stock_location.usage == 'internal' and stock_location.is_magento_source == True and magento_backend != False:
            try:
                params = {
                    'source': {
                        'name': vals['name'],
                        'source_code': 'odoo_location_' + str(stock_location.id),
                        'enabled': True,
                        'contact_name': stock_location.partner_id.name,
                        'email': stock_location.partner_id.email,
                        'phone': stock_location.partner_id.phone,
                        'postcode': stock_location.post_code,
                        'country_id': stock_location.country_id.code
                    }
                }

                client = Client(magento_backend.web_url, magento_backend.access_token, True)
                client.post('rest/V1/inventory/sources', arguments=params)
            except Exception as e:
                raise UserError(('Not create source to magento - %s') % tools.ustr(e))
        elif stock_location.usage != 'internal' and stock_location.is_magento_source == True:
            raise Warning(
                ("You can't create this source on magento if this type of location isn't an internal location"))
        return stock_location

    def update_quantity_product_location(self, stock_location_id, magento_backend):
        stock_quant = self.env['stock.quant'].search([('location_id', '=', stock_location_id)])
        for e in stock_quant:
            if e.product_id.on_magento == True:
                try:
                    params = {
                        "sourceItems": [
                            {
                                "sku": e.product_id.default_code,
                                "source_code": "odoo_location_" + str(e.location_id.id),
                                "quantity": e.quantity,
                                "status": 1
                            }
                        ]
                    }
                    client = Client(magento_backend.web_url, magento_backend.access_token, True)
                    client.post('rest/V1/inventory/source-items', arguments=params)
                except Exception as a:
                    raise UserError(('Can not update quantity product on source magento - %s') % tools.ustr(a))

    @api.multi
    def write(self, vals):
        magento_backend = request.env['magento.backend'].search([], limit=1)
        if magento_backend == False:
            return super(StockLocation, self).write(vals)
        else:
            if 'active' not in vals:
                super(StockLocation, self).write(vals)
                if self.usage == 'internal' and self.is_magento_source == True:
                    try:
                        params = {
                            'source': {
                                'name': self.name,
                                'contact_name': self.partner_id.name,
                                'email': self.partner_id.email,
                                'phone': self.partner_id.phone,
                                'postcode': self.post_code,
                                'country_id': self.country_id.code,
                                'enabled': True
                            }
                        }

                        resource_path = 'rest/V1/inventory/sources/' + 'odoo_location_' + str(self.id)
                        client = Client(magento_backend.web_url, magento_backend.access_token, True)
                        client.put(resource_path=resource_path, arguments=params)
                    except Exception as e:
                        raise UserError(('Can not write source to magento - %s') % tools.ustr(e))
                    self.update_quantity_product_location(self.id, magento_backend)
                elif self.usage == 'internal' and self.is_magento_source == False and 'is_magento_source' in vals:
                    try:
                        params = {
                            'source': {
                                'name': self.name,
                                'enabled': False,
                                'country_id': self.country_id.code,
                                'postcode': self.post_code,
                            }
                        }
                        resource_path = 'rest/V1/inventory/sources/' + 'odoo_location_' + str(self.id)
                        client = Client(magento_backend.web_url, magento_backend.access_token, True)
                        client.put(resource_path=resource_path, arguments=params)
                    except Exception as e:
                        raise UserError(('Can not update source to magento - %s') % tools.ustr(e))
                elif self.usage == 'internal' and self.is_magento_source == False and 'is_magento_source' not in vals:
                    return super(StockLocation, self).write(vals)
                elif self.usage != 'internal' and self.is_magento_source == True:
                    raise Warning(
                        ("You can't update this source on magento if this type of location isn't an internal location"))
            else:
                if vals['active'] == False:
                    super(StockLocation, self).write(vals)
                    self.is_magento_source = False
                    try:
                        params = {
                            'source': {
                                'name': self.name,
                                'enabled': False,
                                'country_id': self.country_id.code,
                                'postcode': self.post_code,
                            }
                        }
                        resource_path = 'rest/V1/inventory/sources/' + 'odoo_location_' + str(self.id)
                        client = Client(magento_backend.web_url, magento_backend.access_token, True)
                        client.put(resource_path=resource_path, arguments=params)
                    except Exception as e:
                        raise UserError(('Can not update source to magento - %s') % tools.ustr(e))
                else:
                    return super(StockLocation, self).write(vals)

    @api.multi
    def unlink(self):
        for rec in self:
            magento_backend = request.env['magento.backend'].search([], limit=1)
            if magento_backend == False:
                return super(StockLocation, self).unlink()
            else:
                if rec.usage == 'internal' and rec.is_magento_source == True:
                    try:
                        params = {
                            'source': {
                                'name': rec.name,
                                'enabled': False,
                                'country_id': rec.country_id.code,
                                'postcode': rec.post_code,
                            }
                        }
                        resource_path = 'rest/V1/inventory/sources/' + 'odoo_location_' + str(rec.id)
                        client = Client(magento_backend.web_url, magento_backend.access_token, True)
                        client.put(resource_path=resource_path, arguments=params)
                    except Exception as e:
                        raise UserError(('Can not delete source to magento - %s') % tools.ustr(e))
                return super(StockLocation, self).unlink()
