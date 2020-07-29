import base64

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.tools.mimetypes import guess_mimetype
from ...utils.magento.product import Product


class MagentoSyncOdoo(models.Model):
    _inherit = "product.template"

    on_magento = fields.Boolean(string='Sync Magento', default=False)
    magento_attr_set = fields.Many2one('magento.attribute.set', 'Magento Attribute Set')
    magento_ok = fields.Boolean(default=False)
    type = fields.Selection(
        selection_add=[('magento_simple', 'Magento Simple'),
                       ('magento_virtual', 'Magento Virtual'),
                       ('magento_downloadable', 'Magento Downloadable'),
                       ('magento_configurable', 'Magento Configurable'),
                       ('magento_grouped', 'Magento Grouped'),
                       ('magento_bundle', 'Magento Bundle')]
    )

    # _sql_constraints = [
    #     ('code_uniq', 'unique (default_code)', "Code already exists !"),
    # ]

    @api.model
    def create(self, values):
        # check unique code
        if 'default_code' in values and values['default_code'] != False:
            count = 0
            self.env.cr.execute(
                """select default_code from product_template WHERE default_code=%s""", (values['default_code'],))
            code = self.env.cr.fetchall()
            if len(code) > 0:
                raise Warning(_('Code %s Is Already Exist') % code[0][0])
            self.env.cr.execute(
                """select default_code from product_template where LOWER(default_code)=LOWER(%s)""",
                (values['default_code'],))
            duplicate_code = self.env.cr.fetchall()
            if len(duplicate_code) > 0:
                raise Warning(_('Code %s Is Duplicate Case With Exist Code!') % values['default_code'])
        if 'm2_info_attr_set' in values:
            attr_set_id = self.env['magento.attribute.set'].sudo().search(
                [('attribute_set_id', '=', values.get('m2_info_attr_set'))], limit=1).id
            if attr_set_id:
                values.update({
                    'on_magento': True,
                    'magento_ok': True,
                    'magento_attr_set': attr_set_id
                })
        res = super(MagentoSyncOdoo, self).create(values)
        if res.on_magento and 'm2_info_attr_set' not in values and 'm2_info_cancel' not in values:
            if not (res.type == 'product'):
                raise Warning(_('Need Product Storable For Magento Sync'))
            if not res.default_code or not res.magento_attr_set:
                raise Warning(_('Need InternalReferenceCode/MagentoSetID For Magento Sync'))
            magento = self.env['magento.backend'].search([('id', '!=', False)], limit=1, order='id DESC')
            if magento and res.default_code:
                product = Product(magento.web_url, magento.access_token, True)
                if product:
                    if res.active == True:
                        active = 1
                    else:
                        active = 0
                    body = {
                        "product": {
                            "sku": res.default_code,
                            "name": res.name,
                            "attribute_set_id": res.magento_attr_set.attribute_set_id,
                            "price": res.list_price,
                            "status": active,
                            "visibility": 4,
                            "type_id": "simple",
                            "weight": "0.5",
                            "extension_attributes": {
                                "stock_item": {
                                    "qty": "0",
                                    "is_in_stock": True
                                }
                            }
                        }
                    }
                    if res.image:
                        image = res.image.replace(b"\n", b"").decode('ascii')
                        mimetype = self._get_image_type(res.image)
                        # decode = base64.b64decode(res.image)
                        # mimetype = guess_mimetype(decode, default='image/png')
                        # if mimetype not in ('image/jpeg', 'image/png', 'image/gif'):
                        #     raise Warning(_('Image Format Not Support On Magento '))
                        body['product'].update({
                            "media_gallery_entries": [
                                {
                                    "media_type": "image",
                                    "label": "Image",
                                    "position": 1,
                                    "disabled": False,
                                    "types": [
                                        "image",
                                        "small_image",
                                        "thumbnail"
                                    ],
                                    "content": {
                                        "base64EncodedData": image,
                                        "type": mimetype,
                                        "name": "Default"
                                    }
                                }
                            ],
                        })
                    if len(res.product_image_ids) > 0:
                        if not res.image:
                            body['product'].update({
                                "media_gallery_entries": []})
                        count = 1
                        for img in res.product_image_ids:
                            count += 1
                            if img.image:
                                extra_image = img.image.replace(b"\n", b"").decode('ascii')
                                extra_mimetype = self._get_image_type(img.image)
                                # extra_decode = base64.b64decode(img.image)
                                # extra_mimetype = guess_mimetype(extra_decode, default='image/png')
                                # if extra_mimetype not in ('image/jpeg', 'image/png', 'image/gif'):
                                #     raise Warning(_('Image Format Not Support On Magento '))
                                body['product']['media_gallery_entries'].append(
                                    {
                                        "media_type": "image",
                                        "label": "Image",
                                        "position": count,
                                        "disabled": False,
                                        "content": {
                                            "base64EncodedData": extra_image,
                                            "type": extra_mimetype,
                                            "name": img.name
                                        }
                                    }
                                )
                    if res.description_sale:
                        body['product'].update({"custom_attributes": [{
                            "attribute_code": "short_description",
                            "value": res.description_sale
                        }]})
                    # Call Magento API
                    try:
                        magento_prd = product.create_magento_product(body)
                        # All Store Magento View
                        product.create_magento_product_all(body)
                    except Exception as e:
                        raise Warning(_("Some %s contains incorrect values.") % e)
                    try:
                        if magento_prd['id'] is not None:
                            res.magento_ok = True
                    except Exception as e:
                        raise Warning(_("Some %s contains incorrect values.Try Again!") % e)
        return res

    @api.one
    def write(self, values):
        # check onchange
        onchange = values
        sku = self.default_code
        on_magento = self.on_magento
        # check unique code
        if 'default_code' in values and values['default_code'] != False:
            if values['default_code'] != sku:
                self.env.cr.execute(
                    """select default_code from product_template WHERE default_code=%s""", (values['default_code'],))
                code = self.env.cr.fetchall()
                if len(code) > 0:
                    raise Warning(_('Product Code %s Existed') % code[0][0])
                # check lower-case, upper-case
                self.env.cr.execute(
                    """select default_code from product_template where LOWER(default_code)=LOWER(%s)""",
                    (values['default_code'],))
                duplicate_code = self.env.cr.fetchall()
                if len(duplicate_code) > 0:
                    raise Warning(_('Product Code %s Existed!') % values['default_code'])
        prod = super(MagentoSyncOdoo, self).write(values)
        body = {"product": {}}
        check = 0
        # Find magento config
        # Need to ensure one to not call back api odoo-magento
        if 'm2_info_cancel' not in values:
            magento = self.env['magento.backend'].search([('id', '!=', False)], limit=1, order='id DESC')
            if magento:
                product = Product(magento.web_url, magento.access_token, True)
            else:
                raise Warning(_('Not Magento Configure'))
            if self.magento_ok:
                if on_magento:
                    if not (self.type == 'product'):
                        raise Warning(_('Need Product Storable For Magento Integration'))
                    if 'on_magento' in onchange:
                        # Delete magento product
                        product.delete_magento_product(sku)
                        # values.update({'magento_ok': False})
                        self.env.cr.execute(
                            """update product_template set magento_ok = FALSE WHERE id=%s""", (self.id,))
                    else:
                        if 'name' in onchange:
                            check += 1
                            body['product'].update({
                                'name': onchange['name']
                            })
                        if 'active' in onchange:
                            check += 1
                            if onchange['active'] == True:
                                active = 1
                            else:
                                active = 0
                            body['product'].update({
                                'status': active
                            })
                        # if 'default_code' in onchange:
                        #     body['product'].update({
                        #         'sku': onchange['default_code']
                        #     })
                        if 'list_price' in onchange:
                            check += 1
                            body['product'].update({
                                'price': onchange['list_price']
                            })
                        if 'magento_attr_set' in onchange:
                            check += 1
                            attribute_set_id = self.env['magento.attribute.set'].sudo().search(
                                [('id', '=', onchange['magento_attr_set'])]).attribute_set_id
                            body['product'].update({
                                'attribute_set_id': attribute_set_id
                            })
                        if 'image_medium' in onchange or 'product_image_ids' in onchange:
                            check += 1
                            if self.image == False:
                                body['product'].update({
                                    "media_gallery_entries": []})
                            else:
                                image = self.image.replace(b"\n", b"").decode('ascii')
                                mimetype = self._get_image_type(self.image)
                                # decode = base64.b64decode(self.image)
                                # image_data = io.BytesIO(decode)
                                # mimetype = guess_mimetype(decode, default='image/png')
                                # if mimetype not in ('image/jpeg', 'image/png', 'image/gif'):
                                #     raise Warning(_('Image Format Not Support On Magento '))
                                body['product'].update({
                                    "media_gallery_entries": [
                                        {
                                            "media_type": "image",
                                            "label": "Image",
                                            "position": 1,
                                            "disabled": False,
                                            "types": [
                                                "image",
                                                "small_image",
                                                "thumbnail"
                                            ],
                                            "content": {
                                                "base64EncodedData": image,
                                                "type": mimetype,
                                                "name": "Default"
                                            }
                                        }
                                    ],
                                })
                            if len(self.product_image_ids) > 0:
                                position = 1
                                for img in self.product_image_ids:
                                    position += 1
                                    if img.image:
                                        extra_image_edit = img.image.replace(b"\n", b"").decode('ascii')
                                        extra_mimetype_edit = self._get_image_type(img.image)
                                        # extra_decode_edit = base64.b64decode(img.image)
                                        # extra_mimetype_edit = guess_mimetype(extra_decode_edit, default='image/png')
                                        # if extra_mimetype_edit not in ('image/jpeg', 'image/png', 'image/gif'):
                                        #     raise Warning(_('Image Format Not Support On Magento '))
                                        body['product']['media_gallery_entries'].append(
                                            {
                                                "media_type": "image",
                                                "label": "Image",
                                                "position": position,
                                                "disabled": False,
                                                "content": {
                                                    "base64EncodedData": extra_image_edit,
                                                    "type": extra_mimetype_edit,
                                                    "name": img.name
                                                }
                                            }
                                        )
                        if 'description_sale' in onchange:
                            check += 1
                            body['product'].update({"custom_attributes": [{
                                "attribute_code": "short_description",
                                "value": self.description_sale
                            }]})
                        # Call Magento API
                        try:
                            if check > 0:
                                a = product.update_magento_product(sku, body)
                                if a.status_code != 200:
                                    raise Warning('Some values contains incorrect values.Try again!')
                                a = product.update_magento_product_all(sku, body)
                                if a.status_code != 200:
                                    raise Warning('Some values contains incorrect values.Try again!')
                        except Exception as e:
                            raise Warning(_("%s.") % e)
                if not on_magento:
                    if 'on_magento' in onchange:
                        if not self.default_code:
                            raise Warning(_('Need InternalReferenceCode/MagentoSetID For Magento Sync'))
                        else:
                            if not (self.type == 'product'):
                                raise Warning(_('Need Product Storable For Magento Sync'))
                            if self.active == True:
                                active = 1
                            else:
                                active = 0
                            new_sku = self.default_code
                            body['product'].update({
                                "sku": self.default_code,
                                "name": self.name,
                                "attribute_set_id": self.magento_attr_set.attribute_set_id,
                                "price": self.list_price,
                                "status": active,
                                "visibility": 4,
                                "type_id": "simple",
                                "weight": "0.5",
                                "extension_attributes": {
                                    "stock_item": {
                                        "qty": "0",
                                        "is_in_stock": True
                                    }
                                }
                            }
                            )
                            if self.image:
                                image = self.image.replace(b"\n", b"").decode('ascii')
                                mimetype = self._get_image_type(self.image)
                                # decode = base64.b64decode(self.image)
                                # mimetype = guess_mimetype(decode, default='image/png')
                                # if mimetype not in ('image/jpeg', 'image/png', 'image/gif'):
                                #     raise Warning(_('Image Format Not Support On Magento '))
                                body['product'].update({
                                    "media_gallery_entries": [
                                        {
                                            "media_type": "image",
                                            "label": "Image",
                                            "position": 1,
                                            "disabled": False,
                                            "types": [
                                                "image",
                                                "small_image",
                                                "thumbnail"
                                            ],
                                            "content": {
                                                "base64EncodedData": image,
                                                "type": mimetype,
                                                "name": "Default"
                                            }
                                        }
                                    ],
                                })
                            if len(self.product_image_ids) > 0:
                                if not self.image:
                                    body['product'].update({
                                        "media_gallery_entries": []})
                                count = 1
                                for img in self.product_image_ids:
                                    count += 1
                                    extra_image = img.image.replace(b"\n", b"").decode('ascii')
                                    extra_mimetype = self._get_image_type(img.image)
                                    # extra_decode = base64.b64decode(img.image)
                                    # extra_mimetype = guess_mimetype(extra_decode, default='image/png')
                                    # if extra_mimetype not in ('image/jpeg', 'image/png', 'image/gif'):
                                    #     raise Warning(_('Image Format Not Support On Magento '))
                                    body['product']['media_gallery_entries'].append(
                                        {
                                            "media_type": "image",
                                            "label": "Image",
                                            "position": count,
                                            "disabled": False,
                                            "content": {
                                                "base64EncodedData": extra_image,
                                                "type": extra_mimetype,
                                                "name": img.name
                                            }
                                        }
                                    )
                            if self.description_sale:
                                body['product'].update({"custom_attributes": [{
                                    "attribute_code": "short_description",
                                    "value": self.description_sale
                                }]})
                            # Call Magento API
                            try:
                                magento_sync = product.update_magento_product(new_sku, body)
                                # all store magento view
                                product.update_magento_product_all(new_sku, body)
                                try:
                                    if magento_sync.json()['id'] is not None:
                                        # values.update({'magento_ok': True})
                                        self.env.cr.execute(
                                            """update product_template set magento_ok = TRUE WHERE id=%s""", (self.id,))
                                except Exception as e:
                                    raise Warning(_("Some %s contains incorrect values.Try Again!") % e)
                            except Exception as e:
                                raise Warning(_("Some %s contains incorrect values.") % e)
                # # Call Magento API
                # product.update_magento_product(sku, body)
            if not self.magento_ok:
                if 'on_magento' in onchange:
                    if not (self.type == 'product'):
                        raise Warning(_('Need Product Storable For Magento Sync'))
                    if self.active == True:
                        active = 1
                    else:
                        active = 0
                    new_sku = self.default_code
                    body['product'].update({
                        "sku": self.default_code,
                        "name": self.name,
                        "attribute_set_id": self.magento_attr_set.attribute_set_id,
                        "price": self.list_price,
                        "status": active,
                        "visibility": 4,
                        "type_id": "simple",
                        "weight": "0.5",
                        "extension_attributes": {
                            "stock_item": {
                                "qty": "0",
                                "is_in_stock": True
                            }
                        }
                    }
                    )
                    if self.image:
                        image = self.image.replace(b"\n", b"").decode('ascii')
                        mimetype = self._get_image_type(self.image)
                        # decode = base64.b64decode(self.image)
                        # mimetype = guess_mimetype(decode, default='image/png')
                        # if mimetype not in ('image/jpeg', 'image/png', 'image/gif'):
                        #     raise Warning(_('Image Format Not Support On Magento '))
                        body['product'].update({
                            "media_gallery_entries": [
                                {
                                    "media_type": "image",
                                    "label": "Image",
                                    "position": 1,
                                    "disabled": False,
                                    "types": [
                                        "image",
                                        "small_image",
                                        "thumbnail"
                                    ],
                                    "content": {
                                        "base64EncodedData": image,
                                        "type": mimetype,
                                        "name": "Default"
                                    }
                                }
                            ],
                        })
                    if len(self.product_image_ids) > 0:
                        if not self.image:
                            body['product'].update({
                                "media_gallery_entries": []})
                        count = 1
                        for img in self.product_image_ids:
                            count += 1
                            if img.image:
                                extra_image = img.image.replace(b"\n", b"").decode('ascii')
                                extra_mimetype = self._get_image_type(self.image)
                                # extra_decode = base64.b64decode(img.image)
                                # extra_mimetype = guess_mimetype(extra_decode, default='image/png')
                                # if extra_mimetype not in ('image/jpeg', 'image/png', 'image/gif'):
                                #     raise Warning(_('Image Format Not Support On Magento '))
                                body['product']['media_gallery_entries'].append(
                                    {
                                        "media_type": "image",
                                        "label": "Image",
                                        "position": count,
                                        "disabled": False,
                                        "content": {
                                            "base64EncodedData": extra_image,
                                            "type": extra_mimetype,
                                            "name": img.name
                                        }
                                    }
                                )
                    if self.description_sale:
                        body['product'].update({"custom_attributes": [{
                            "attribute_code": "short_description",
                            "value": self.description_sale
                        }]})
                    # Call Magento API
                    try:
                        magento_sync_after = product.update_magento_product(new_sku, body)
                        # All store magento view
                        product.update_magento_product_all(new_sku, body)
                        try:
                            if magento_sync_after.json()['id'] is not None:
                                # values.update({'magento_ok': True})
                                self.env.cr.execute(
                                    """update product_template set magento_ok = TRUE WHERE id=%s""", (self.id,))
                        except Exception as e:
                            raise Warning(_("Some %s contains incorrect values.Try Again!") % e)
                    except Exception as e:
                        raise Warning(_("%s.") % e)

        return prod

    @api.multi
    def unlink(self):
        """ Delete Odoo Product On Delete Magento """
        if self.on_magento:
            sku = self.default_code
            magento = self.env['magento.backend'].search([('id', '!=', False)], limit=1, order='id DESC')
            product = Product(magento.web_url, magento.access_token, True)
            if product:
                # Delete magento product
                try:
                    product.delete_magento_product(sku)
                    product.delete_magento_product_all(sku)
                except Exception as e:
                    'Sh@dowWalker'
        result = super(MagentoSyncOdoo, self).unlink()
        return result

    def _get_image_type(self, image):
        extra_decode = base64.b64decode(image)
        mimetype = guess_mimetype(extra_decode)
        if mimetype == 'application/octet-stream':
            mimetype = 'image/jpeg'
        if mimetype not in ('image/jpeg', 'image/png', 'image/gif'):
            raise Warning(_('Image Format Not Support On Magento '))
        return mimetype


class MagentoSyncAttrSet(models.Model):
    _name = "magento.attribute.set"

    name = fields.Char()
    attribute_set_id = fields.Integer()
    attribute_set_name = fields.Char()
    sort_order = fields.Integer()
    entity_type_id = fields.Integer()
    last_update_at = fields.Date('Created At (on Odoo)')
