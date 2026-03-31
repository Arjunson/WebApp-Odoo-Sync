from odoo import models, fields, api

class MiniProductExt(models.Model):
    _inherit = 'mini.product'

    x_external_id = fields.Char(string='Web App ID', index=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('sync_from_api'):
            from ..services.sync_service import SyncService
            for rec in records:
                if not rec.x_external_id:
                    SyncService(self.env).push_product_to_api(rec)
        return records

    def write(self, vals):
        # If quantity updates, we might want to push stock to API
        qties_before = {rec.id: rec.quantity for rec in self} if 'quantity' in vals else {}

        res = super().write(vals)

        if not self.env.context.get('sync_from_api'):
            from ..services.sync_service import SyncService
            for rec in self:
                # Push product metadata changes
                if any(f in vals for f in ['name', 'price', 'cost']):
                    SyncService(self.env).push_product_to_api(rec)
                
                # Push stock changes
                if 'quantity' in vals and qties_before.get(rec.id) != rec.quantity:
                    SyncService(self.env).push_stock_to_api(rec)

        return res
