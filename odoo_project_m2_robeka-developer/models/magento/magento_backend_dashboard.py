import json

from odoo import models, fields, api


class MagentoBackendDashboard(models.Model):
    _inherit = "magento.backend"

    @api.one
    def _kanban_dashboard(self):
        self.kanban_dashboard = json.dumps(self.get_magento_backend_dashboard_datas())

    kanban_dashboard = fields.Text(compute='_kanban_dashboard')
    color = fields.Integer()

    @api.multi
    def get_magento_backend_dashboard_datas(self):
        magento_backend_id = self.id
        title = ''
        number_website = len(self.website_ids)
        self.env.cr.execute("""SELECT COUNT(DISTINCT(id)) FROM magento_store WHERE backend_id = %s""",
                            (magento_backend_id,))
        number_store = self.env.cr.fetchone()[0]
        self.env.cr.execute("""SELECT COUNT(DISTINCT(id)) FROM magento_storeview  WHERE backend_id = %s""",
                            (magento_backend_id,))
        number_store_view = self.env.cr.fetchone()[0]

        return {
            'number_website': number_website,
            'number_store': number_store,
            'number_store_view': number_store_view,
            'title': title,
        }
