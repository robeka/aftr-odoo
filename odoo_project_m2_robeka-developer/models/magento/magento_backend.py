import datetime

import math

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
from ...utils.magento.product import Product
from ...utils.magento.rest import Client


def get_current_page(total_count, page_size):
    total_page = total_count / page_size
    if 0 < total_page < 1:
        total_page = 1
    else:
        total_page = math.ceil(total_page)

    return total_page


class MagentoBackend(models.Model):
    _name = "magento.backend"

    name = fields.Char(string='Name', required=True)
    version = fields.Selection(selection=([('Magento 2.3', '2.3'), ('Magento 2.2', '2.2')]), default='Magento 2.3',
                               string='Version', required=True)
    web_url = fields.Char(
        string='Url',
        required=True,
        help="Url to magento application",
    )
    access_token = fields.Char(string='Token', required=True, help="Access token to magento Integration")

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
    )
    website_ids = fields.One2many('magento.website', 'backend_id', string='Website', readonly=True, )

    prefix_sale_order = fields.Char("Prefix Sale Order")

    _sql_constraints = [('uniq_web_url', 'unique(web_url)', "The Url must be unique !")]

    @api.model
    def create(self, values):
        record = super(MagentoBackend, self).create(values)
        if values.get('web_url') and values.get('access_token'):
            access_token = values.get('access_token')
            url = values.get('web_url')
            self.pull_magento_backend(url, access_token, record.id)

        return record

    @api.multi
    def unlink(self):
        self.env.cr.execute(""" DELETE FROM magento_website WHERE TRUE;
                                DELETE FROM magento_backend WHERE TRUE;
                                DELETE FROM magento_storeview WHERE TRUE;
                                DELETE FROM magento_store WHERE TRUE;
                                DELETE FROM res_partner_category WHERE TRUE;""")

    def fetch_attribute_set(self):
        # get from config
        # backend_id = self.id
        url = self.web_url
        token = self.access_token
        # self.pull_magento_backend(url, token, backend_id)
        product = Product(url, token, True)
        AttributeSet = self.env['magento.attribute.set'].sudo()
        current_attr_set = self.env['magento.attribute.set'].sudo().search([])
        firt_pull = len(current_attr_set)
        if product:
            try:
                product_attr_sets = product.list_attribute_set(condition='0')
            except ValueError as e:
                raise ValueError(_("Some %s contains incorrect values.") % e)
            if len(product_attr_sets['items']) > 0:
                if firt_pull == 0:
                    for item in product_attr_sets['items']:
                        # first pull
                        try:
                            AttributeSet.create({
                                'name': item['attribute_set_name'],
                                'attribute_set_id': item['attribute_set_id'],
                                'attribute_set_name': item['attribute_set_name'],
                                'sort_order': item['sort_order'],
                                'entity_type_id': item['entity_type_id'],
                                'last_update_at': datetime.datetime.today(),
                            })
                        except ValueError as e:
                            raise ValueError(_("Some %s contains incorrect values.") % e)
                # Not First Pull
                if firt_pull != 0:
                    # Delete old attr
                    for a in current_attr_set:
                        a.unlink()
                    # Create new
                    for item in product_attr_sets['items']:
                        try:
                            AttributeSet.create({
                                'name': item['attribute_set_name'],
                                'attribute_set_id': item['attribute_set_id'],
                                'attribute_set_name': item['attribute_set_name'],
                                'sort_order': item['sort_order'],
                                'entity_type_id': item['entity_type_id'],
                                'last_update_at': datetime.datetime.today(),
                            })
                        except ValueError as e:
                            raise ValueError(_("Some %s contains incorrect values.") % e)

        else:
            return ValueError(_('Some Error Magento Configure '))

    def pull_magento_backend(self, url, access_token, backend_id):
        try:
            client = Client(url, access_token, True)
            websites = client.get('rest/V1/store/websites', '')
            website_magento_id = []
            website_odoo_id = []
            check_len_arr = False
            for website in websites:
                self.env.cr.execute("""INSERT INTO magento_website (name, code,backend_id,external_id,create_date, write_date,create_uid,write_uid)
                                        VALUES (%s, %s, %s, %s, %s ,%s, %s, %s) ON CONFLICT (backend_id, external_id) DO UPDATE SET (name,code)=(EXCLUDED.name,EXCLUDED.code) RETURNING id""",
                                    (website['name'], website['code'], backend_id, website['id'],
                                     datetime.datetime.today(), datetime.datetime.today(), self.env.uid, self.env.uid))

                # web = self.env['magento.website'].create({
                #     'name': website['name'],
                #     'code': website['code'],
                #     'backend_id': backend_id,
                #     'external_id': website['id']
                # })
                web_id = self.env.cr.fetchall()[0][0]
                website_magento_id.append(website['id'])
                website_odoo_id.append(web_id)

            # filter(lambda x, y: x == y, website_odoo_id, website_magento_id)

            if len(website_odoo_id) == len(website_magento_id):
                check_len_arr = True

            # store
            store_groups = client.get('rest/V1/store/storeGroups', '')
            for store_group in store_groups:
                self.env.cr.execute("""INSERT INTO magento_store (name, code, root_category_id, website_id, backend_id, external_id)
                                       VALUES (%s, %s, %s, %s, %s, %s ) ON CONFLICT (backend_id, external_id) DO UPDATE SET (name, code, root_category_id, website_id) = (EXCLUDED.name, EXCLUDED.code, EXCLUDED.root_category_id, EXCLUDED.website_id)""",
                                    (store_group['name'], store_group['code'],
                                     store_group['root_category_id'], website_odoo_id[
                                         website_magento_id.index(store_group['website_id'])] if check_len_arr else -1,
                                     backend_id, store_group['id']))
            # store view
            store_views = client.get('/rest/V1/store/storeViews', '')
            for store_view in store_views:
                self.env.cr.execute("""INSERT INTO magento_storeview (name,code,store_id,website_id,is_active,backend_id, external_id)
                                       VALUES (%s, %s, %s, %s, %s, %s, %s ) ON CONFLICT (backend_id, external_id) DO UPDATE SET (name, code, store_id, website_id, is_active) =(EXCLUDED.name, EXCLUDED.code, EXCLUDED.store_id, EXCLUDED.website_id, EXCLUDED.is_active)  """,
                                    (store_view['name'], store_view['code'],
                                     client.adapter_magento_id('magento_store', backend_id,
                                                               store_view['store_group_id']),
                                     website_odoo_id[
                                         website_magento_id.index(store_view['website_id'])] if check_len_arr else -1,
                                     store_view['is_active'], backend_id, store_view['id']))
        except Exception as e:
            raise UserError(_('Not pull data from magento - magento.backend %s') % tools.ustr(e))
