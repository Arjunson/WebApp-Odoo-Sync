from odoo import models, fields, api

class SyncConfig(models.Model):
    _name = 'sync.config'
    _description = 'API Sync Configuration'

    name = fields.Char(default='API Sync Settings', required=True)
    api_base_url = fields.Char(string="API Base URL", required=True, help="e.g. http://127.0.0.1:8000/api/v1")
    api_token = fields.Char(string="API Token", required=True)
    
    sync_customers = fields.Boolean(string="Sync Customers", default=True)
    sync_products = fields.Boolean(string="Sync Products", default=True)
    sync_orders = fields.Boolean(string="Sync Orders", default=True)

    @api.model
    def get_config(self):
        """Return the singleton config record, creating one if it doesn't exist."""
        config = self.search([], limit=1)
        if not config:
            config = self.create({
                'name': 'API Sync Settings',
                'api_base_url': 'http://127.0.0.1:8000/api/v1',
                'api_token': 'secret-token'
            })
        return config

    def action_sync_customers(self):
        """Trigger manual customer sync"""
        from ..services.sync_service import SyncService
        SyncService(self.env).sync_customers_from_api()

    def action_sync_products(self):
        """Trigger manual product sync"""
        from ..services.sync_service import SyncService
        SyncService(self.env).sync_products_from_api()

    def action_sync_orders(self):
        """Trigger manual order sync"""
        from ..services.sync_service import SyncService
        SyncService(self.env).sync_orders_from_api()
