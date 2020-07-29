from odoo import api, fields, models


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    network = fields.Char(string="Network")
    wakeup_number = fields.Char(string="Wake up number")
    camera_password = fields.Char(string="Camera Password")
    imei = fields.Char(string="IMEI")
    tutk = fields.Char(string="TUTK")
    msisdn = fields.Char(string="MSISDN")
