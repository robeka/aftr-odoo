from ..magento.rest import Client


class Product(Client):
    __slots__ = ()

    def create_magento_product(self, body):
        return self.post('rest/V1/products/', body)

    def create_magento_product_all(self, body):
        return self.post('rest/all/V1/products/', body)

    def update_magento_product(self, sku, body):
        return self.put('rest/V1/products/' + sku, body)

    def update_magento_product_all(self, sku, body):
        return self.put('rest/all/V1/products/' + sku, body)

    def delete_magento_product(self, sku):
        return self.delete('rest/V1/products/' + sku)

    def delete_magento_product_all(self, sku):
        return self.delete('rest/all/V1/products/' + sku)

    def list_attribute_set(self, condition):
        return self.get('rest/V1/products/attribute-sets/sets/list',
                        'searchCriteria=' + condition)

    # def list_gt_updated_attr_set(self, updated_at):
    #     return self.get('rest/V1/products/attribute-sets/sets/list',
    #                      'searchCriteria[filter_groups][0][filters][0][field]=updated_at&'
    #                      'searchCriteria[filter_groups][0][filters][0][value]=' + str(updated_at) + '&' +
    #                      'searchCriteria[filter_groups][0][filters][0][condition_type]=gt&')
