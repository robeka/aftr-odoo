from odoo import models, api, fields
from odoo.http import request
from ...utils.magento.rest import Client


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if res.is_company:
            self.sync_data_partner_company(res)
        elif res.parent_id:
            self.sync_data_partner_company(res.parent_id)
        return res

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        for rec in self:
            if rec.is_company:
                self.sync_data_partner_company(rec)
            elif rec.parent_id:
                self.sync_data_partner_company(rec.parent_id)
        return res

    def sync_data_partner_company(self, company):
        if company:
            magento_backend = request.env['magento.backend'].search([], limit=1)
            client = Client(magento_backend.web_url, magento_backend.access_token, True)
            child_ids = []
            if company.child_ids:
                for child in company.child_ids:
                    data_customer = {
                        'name': child.name,
                        'is_company': child.is_company,
                        'function': child.function,  # Job position
                        'title': child.title.name if child.title else False,  # Danh xưng, Miss, Mr, Doctor, Professor
                        'street': child.street,
                        'streets': child.street2,
                        'city': child.city,
                        'state': child.state_id.name if child.state_id else False,
                        'zip': child.zip,
                        'country_id': child.country_id.code if child.country_id else False,
                        'vat': child.vat,  # Tax of company/customer
                        'phone': child.phone,
                        'mobile': child.mobile,
                        'email': child.email,
                        'website': child.website,
                        'lang': child.lang,
                        'comment': child.comment,
                        'customer': child.customer,
                        'supplier': child.supplier,
                        'type': child.type  # contact,invoice,delivery,orther,private
                    }
                    child_ids.append(data_customer)

            params = {
                'odoo_id': company.id,
                'name': company.name,
                'is_company': company.is_company,
                'street': company.street,
                'streets': company.street2,
                'city': company.city,
                'state': company.state_id.name if company.state_id else False,
                'zip': company.zip,
                'country_id': company.country_id.code if company.country_id else False,
                'vat': company.vat,  # Tax of company
                'phone': company.phone,
                'mobile': company.mobile,
                'email': company.email,
                'website': company.website,
                'lang': company.lang,
                'comment': company.comment,
                'customer': company.customer,
                'supplier': company.supplier,
                'child_ids': child_ids,
            }
            final_params = {}
            final_params['data'] = params
            if final_params:
                try:
                    url = 'rest/V1/company/upset'
                    # print('trigger return')
                    client.post(url, arguments=final_params)
                except Exception as e:
                    print(e)

    # id_magento_company = fields.Integer(string='Magento Company ID')

    # @api.multi
    # def write(self, vals):
    #     for rec in self:
    #         if 'id_magento_company' in vals:
    #             company = None
    #             if 'company_type' in vals:
    #                 if vals['company_type'] and vals['company_type'] == 'person':
    #                     company = self.env['res.partner'].sudo().search([('id_magento_company', '=', vals['id_magento_company']), ('company_type', '=', 'company')], limit=1)
    #             elif self.company_type == 'person':
    #                 company = self.env['res.partner'].sudo().search([('id_magento_company', '=', vals['id_magento_company']), ('company_type', '=', 'company')], limit=1)
    #             if company:
    #                 company.sudo().write({
    #                     'child_ids': [(4, rec.id)]
    #                 })
    #                 # vals['partner_id'] = company.id
    #                 # vals.pop('id_magento_company', None)
    #     result = super(ResPartner, self).write(vals)
    #     # for rec in self:
    #     #     stock_location = self.env['stock.location'].sudo().search([('partner_id', '=', rec.id)])
    #     #     for e in stock_location:
    #     #         e.write({
    #     #             'partner_id': rec.id
    #     #         })
    #     return result
    #
    # @api.model
    # def create(self, vals):
    #     res = super(ResPartner, self).create(vals)
    #     if 'id_magento_company' in vals and 'company_type' in vals:
    #         if vals['company_type'] and vals['company_type'] == 'person':
    #             company = self.env['res.partner'].sudo().search([('id_magento_company', '=', vals['id_magento_company']), ('company_type', '=', 'company')], limit=1)
    #             if company:
    #                 company.sudo().write({
    #                     'child_ids': [(4, res.id)]
    #                 })
    #     return res
