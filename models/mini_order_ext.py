from odoo import models, fields, api

class MiniOrderExt(models.Model):
    _inherit = 'mini.order'

    x_external_id = fields.Char(string='Web App ID', index=True, copy=False)

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals and not self.env.context.get('sync_from_api'):
            from ..services.sync_service import SyncService
            for rec in self:
                if rec.x_external_id:
                    SyncService(self.env).push_order_status_to_api(rec)
        return res
