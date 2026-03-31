from odoo import models, fields

class MiniCustomerExt(models.Model):
    _inherit = 'mini.customer'

    x_external_id = fields.Char(string='Web App ID', index=True, copy=False)
