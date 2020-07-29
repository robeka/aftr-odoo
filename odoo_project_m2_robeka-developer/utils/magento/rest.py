# coding: utf-8
try:
    import requests
    import json
except ImportError:
    pass
from odoo.http import request


class Client(object):

    def __init__(self, url, token, verify_ssl=True):
        self._url = url
        self._token = token
        self._verify_ssl = verify_ssl

    def get(self, resource_path, arguments):
        url = '%s/%s' % (self._url, resource_path)
        res = requests.get(
            url, params=arguments, verify=self._verify_ssl,
            headers={'Authorization': 'Bearer ' + self._token, 'Content-Type': 'application/json'}, )
        # res.raise_for_status()
        return res.json()

    def post(self, resource_path, arguments):
        url = '%s/%s' % (self._url, resource_path)
        res = requests.post(
            url, json=arguments, verify=self._verify_ssl,
            headers={'Authorization': 'Bearer %s' % self._token,
                     'Content-Type': 'application/json'})
        # res.raise_for_status()
        return res.json()

    def put(self, resource_path, arguments):
        url = '%s/%s' % (self._url, resource_path)
        res = requests.put(
            url, json=arguments, verify=self._verify_ssl,
            headers={'Authorization': 'Bearer %s' % self._token,
                     'Content-Type': 'application/json'})
        # print(res.text)
        # res.raise_for_status()
        return res

    def delete(self, resource_path):
        url = '%s/%s' % (self._url, resource_path)
        res = requests.delete(
            url, verify=self._verify_ssl,
            headers={'Authorization': 'Bearer %s' % self._token,
                     'Content-Type': 'application/json'})
        # print(res.text)
        # res.raise_for_status()
        return res.json()

    def adapter_magento_id(self, table, backend_id, external_id):
        request.env.cr.execute("SELECT id FROM %s WHERE backend_id=%s AND external_id=%s LIMIT 1" % (
            table.strip("'"), backend_id, external_id))
        magento_ids = request.env.cr.fetchall()[0]
        return magento_ids[0] if magento_ids else -1
