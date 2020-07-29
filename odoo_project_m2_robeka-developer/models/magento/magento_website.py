from odoo import models, fields


class MagentoWebsite(models.Model):
    _name = 'magento.website'
    _inherit = 'magento.binding'
    _description = 'Magento Website'

    _order = 'id ASC'

    name = fields.Char(required=True, readonly=True)
    code = fields.Char(readonly=True)

    store_ids = fields.One2many(
        'magento.store',
        'website_id',
        string='Stores',
        readonly=True,
    )
