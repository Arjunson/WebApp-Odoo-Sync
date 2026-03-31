from odoo import models, fields

class SyncLog(models.Model):
    _name = 'sync.log'
    _description = 'API Sync Log'
    _order = 'timestamp desc'

    name = fields.Char(string="Operation", required=True)
    model = fields.Selection([
        ('mini.customer', 'Customer'),
        ('mini.product', 'Product'),
        ('mini.order', 'Order'),
        ('inventory', 'Inventory')
    ], string="Model", required=True)
    
    external_id = fields.Char(string="External ID")
    direction = fields.Selection([
        ('inbound', 'Inbound (API → Odoo)'),
        ('outbound', 'Outbound (Odoo → API)')
    ], string="Direction", required=True)
    
    state = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed')
    ], string="Status", required=True)
    
    error_message = fields.Text(string="Error Details")
    timestamp = fields.Datetime(default=fields.Datetime.now, readonly=True)
