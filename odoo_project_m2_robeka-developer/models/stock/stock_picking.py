from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError
from odoo.http import request
from ...utils.magento.rest import Client


# from odoo.addons.delivery.models.stock_picking import StockPicking


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_return_picking = fields.Boolean(default=False)

    def _create_shipment(self, sale_order_increment_id, client, move_lines):
        item_id_information = {}
        order_magento = client.get(
            "rest/V1/orders?searchCriteria[filter_groups][0][filters][0][field]=increment_id&searchCriteria[filter_groups][0][filters][0][value]=" +
            sale_order_increment_id, arguments='')
        current_magento_order = order_magento['items'][0]
        for a in current_magento_order["items"]:
            item_id_information[a["sku"]] = a["item_id"]
        data = []
        tracks = []
        serials = []
        data_dict = {}
        serial_dict = {}
        tracks_dict = {}
        for e in move_lines:
            if e.product_id.default_code in item_id_information:
                data.append({
                    "order_item_id": item_id_information[e.product_id.default_code],
                    "qty": str(e.quantity_done)
                })
                if e.product_id.tracking != 'none':
                    if len(e.move_line_ids) > 0:
                        for s in e.move_line_ids:
                            serials.append(
                                {
                                    'serial_id': str(s.lot_id.id),
                                    'serial': s.lot_id.name,
                                    'sku': e.product_id.default_code,
                                    'ref': e.lot_id.ref if s.lot_id.ref else "",
                                    'network': str(s.lot_id.network) if s.lot_id and s.lot_id.network else False,
                                    'wakeup_number': str(s.lot_id.wakeup_number) if s.lot_id and s.lot_id.wakeup_number else False,
                                    'camera_password': str(s.lot_id.camera_password) if s.lot_id and s.lot_id.camera_password else False,
                                    'imei': str(s.lot_id.imei) if s.lot_id and s.lot_id.imei else False,
                                    'tutk': str(s.lot_id.tutk) if s.lot_id and s.lot_id.tutk else False,
                                    'msisdn': str(s.lot_id.msisdn) if s.lot_id and s.lot_id.msisdn else False,
                                }
                            )
        if len(data) > 0:
            data_dict = {str(i): data[i] for i in range(0, len(data))}
        if len(serials) > 0:
            serial_dict = {str(j): serials[j] for j in range(0, len(serials))}
        if self.carrier_id and self.carrier_tracking_ref:
            # check fields exist: 'delivery_type' in model_fields = Model.fields_get()
            if self.carrier_id.delivery_type in ['fedex', 'ups', 'usps', 'dhl']:
                carrier_code = self.carrier_id.delivery_type
            else:
                carrier_code = 'custom'
            tracks.append({
                "track_number": self.carrier_tracking_ref,
                "title": self.carrier_id.name,
                "carrier_code": carrier_code
            })
        if len(tracks) > 0:
            tracks_dict = {str(k): tracks[k] for k in range(0, len(tracks))}
        if len(data) > 0:
            params = {
                "items": data_dict,
                "arguments": {
                    "extension_attributes": {'serials': serial_dict}
                },
                "tracks": tracks_dict
            }
            url = 'rest/V1/order/' + str(current_magento_order['entity_id']) + '/ship'
            client.post(url, arguments=params)
            a =1


    def _validate_return(self, sale_order_origin, move_lines):
        # validate return delivery -> remove serial number in move_line_ids
        magento_backend = request.env['magento.backend'].search([], limit=1)
        client = Client(magento_backend.web_url, magento_backend.access_token, True)
        item_id_information = {}
        order_magento = client.get(
            "rest/V1/orders?searchCriteria[filter_groups][0][filters][0][field]=increment_id&searchCriteria[filter_groups][0][filters][0][value]=" +
            sale_order_origin, arguments='')
        current_magento_order = order_magento['items'][0]
        for a in current_magento_order["items"]:
            item_id_information[a["sku"]] = a["item_id"]
        serial_need_remove = []
        data_dict = {}
        data = []
        params = None
        for e in move_lines:
            if e.product_id.tracking != 'none':
                if len(e.move_line_ids) > 0:
                    for s in e.move_line_ids:
                        serial_need_remove.append(s.lot_id.id)
                if e.product_id.default_code in item_id_information:
                    data.append({
                        "order_item_id": item_id_information[e.product_id.default_code],
                        "qty": str(e.quantity_done)
                    })
        if len(data) > 0:
            data_dict = {str(i): data[i] for i in range(0, len(data))}
        if len(serial_need_remove) > 0:
            params = {
                'orderOrigin': sale_order_origin,
                'serials': ','.join(str(k) for k in serial_need_remove),
                'items': data_dict
            }
        if params:
            try:
                url = 'rest/V1/odoo/removeserial'
                # print('trigger return')
                client.post(url, arguments=params)
                a=1
            except Exception as e:
                print(e)

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        magento_backend = request.env['magento.backend'].search([], limit=1)
        client = Client(magento_backend.web_url, magento_backend.access_token, True)
        for rec in self:
            # create shipment
            if rec.sale_id.id and not rec.is_return_picking:
                try:
                    if magento_backend and rec.sale_id.origin:
                        self._create_shipment(rec.sale_id.origin,
                                              client, rec.move_lines)
                except Exception as e:
                    print(e)
            # remove serial
            if rec.sale_id.id and rec.is_return_picking:
                try:
                    if magento_backend and rec.sale_id.origin:
                        self._validate_return(rec.sale_id.origin, rec.move_lines)
                except Exception as e:
                    print(e)
        # self._update_qty_product_source_magento(client, self.move_line_ids)
        return res

    def action_toggle_is_locked(self):
        magento_backend = request.env['magento.backend'].search([], limit=1)
        if self.sale_id:
            if self.sale_id.origin:
                raise UserError(
                    'You cannot unlock the delivery of the magento synchronization order')
            else:
                super(StockPicking, self).action_toggle_is_locked()
        else:
            super(StockPicking, self).action_toggle_is_locked()


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    code = fields.Char()


class ReturnPickingInherit(models.TransientModel):
    _inherit = 'stock.return.picking'

    def create_returns(self):
        for wizard in self:
            new_picking_id, pick_type_id = wizard._create_returns()
            picking = self.env['stock.picking'].sudo().browse(new_picking_id)
            picking.sudo().write({'is_return_picking': True})
        # Override the context to disable all the potential filters that could have been set previously
        ctx = dict(self.env.context)
        ctx.update({
            'search_default_picking_type_id': pick_type_id,
            'search_default_draft': False,
            'search_default_assigned': False,
            'search_default_confirmed': False,
            'search_default_ready': False,
            'search_default_late': False,
            'search_default_available': False,
        })
        return {
            'name': _('Returned Picking'),
            'view_type': 'form',
            'view_mode': 'form,tree,calendar',
            'res_model': 'stock.picking',
            'res_id': new_picking_id,
            'type': 'ir.actions.act_window',
            'context': ctx,
        }
