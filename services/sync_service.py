import logging
from .api_client import APIClient

_logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, env):
        self.env = env
        self.api = APIClient(env)

    # ─── INBOUND: FETCH FROM API ──────────────────────────────────────

    def sync_customers_from_api(self):
        try:
            data = self.api.get('/customers')
            for item in data:
                ext_id = str(item.get('id'))
                partner = self.env['mini.customer'].search([('x_external_id', '=', ext_id)], limit=1)
                vals = {
                    'name': item.get('name'),
                    'email': item.get('email'),
                    'phone': item.get('phone'),
                    'x_external_id': ext_id,
                }
                if partner:
                    partner.with_context(sync_from_api=True).write(vals)
                else:
                    self.env['mini.customer'].with_context(sync_from_api=True).create(vals)
            self._log_sync('mini.customer', 'inbound', 'success', f"Synced {len(data)} customers")
        except Exception as e:
            self._log_sync('mini.customer', 'inbound', 'failed', str(e))

    def sync_products_from_api(self):
        try:
            data = self.api.get('/products')
            for item in data:
                ext_id = str(item.get('id'))
                product = self.env['mini.product'].search([('x_external_id', '=', ext_id)], limit=1)
                vals = {
                    'name': item.get('name'),
                    'price': item.get('price', 0),
                    'quantity': item.get('stock_quantity', 0),
                    'x_external_id': ext_id,
                }
                if product:
                    product.with_context(sync_from_api=True).write(vals)
                else:
                    self.env['mini.product'].with_context(sync_from_api=True).create(vals)
            self._log_sync('mini.product', 'inbound', 'success', f"Synced {len(data)} products")
        except Exception as e:
            self._log_sync('mini.product', 'inbound', 'failed', str(e))

    def sync_orders_from_api(self):
        try:
            data = self.api.get('/orders', params={'status_filter': 'new'})
            for item in data:
                ext_id = str(item.get('id'))
                order_exists = self.env['mini.order'].search([('x_external_id', '=', ext_id)], limit=1)
                if order_exists:
                    continue
                
                cust_ext_id = str(item.get('customer_id'))
                customer = self.env['mini.customer'].search([('x_external_id', '=', cust_ext_id)], limit=1)
                if not customer:
                    _logger.warning(f"Order {ext_id}: Customer {cust_ext_id} not found, skipping.")
                    continue
                    
                vals = {
                    'customer_id': customer.id,
                    'x_external_id': ext_id,
                    'state': 'draft',
                }
                
                line_vals = []
                for line in item.get('items', []):
                    prod_ext_id = str(line.get('product_id'))
                    product = self.env['mini.product'].search([('x_external_id', '=', prod_ext_id)], limit=1)
                    if product:
                        line_vals.append((0, 0, {
                            'product_id': product.id,
                            'quantity': line.get('quantity', 1),
                            'price': line.get('price', product.price),
                        }))
                vals['order_line_ids'] = line_vals
                
                order = self.env['mini.order'].with_context(sync_from_api=True).create(vals)
                
                # Acknowledge API
                self.api.put(f"/orders/{ext_id}/mark-synced")
                
            self._log_sync('mini.order', 'inbound', 'success', f"Synced {len(data)} orders")
        except Exception as e:
            self._log_sync('mini.order', 'inbound', 'failed', str(e))

    # ─── OUTBOUND: PUSH TO API ────────────────────────────────────────

    def push_product_to_api(self, product):
        try:
            sku = f"{product.name.lower().replace(' ', '-')}-{product.id}"
            payload = {
                'name': product.name,
                'sku': sku,
                'price': float(product.price),
                'stock_quantity': int(product.quantity),
            }
            if product.x_external_id:
                self.api.put(f"/products/{product.x_external_id}", json=payload)
            else:
                resp = self.api.post("/products", json=payload)
                if resp.get('id'):
                    product.x_external_id = str(resp['id'])
            self._log_sync('mini.product', 'outbound', 'success', f"Pushed {product.name}", product.x_external_id)
        except Exception as e:
            self._log_sync('mini.product', 'outbound', 'failed', str(e), product.x_external_id)

    def push_stock_to_api(self, product):
        if not product.x_external_id:
            return
        try:
            payload = {'stock_quantity': int(product.quantity)}
            self.api.put(f"/inventory/update?product_id={product.x_external_id}", json=payload)
            self._log_sync('inventory', 'outbound', 'success', f"Updated stock for {product.name}", product.x_external_id)
        except Exception as e:
            self._log_sync('inventory', 'outbound', 'failed', str(e), product.x_external_id)

    def push_order_status_to_api(self, order):
        if not order.x_external_id:
            return
        try:
            if order.state in ('draft', 'sent'):
                mapped_status = 'new'
            elif order.state == 'done':
                mapped_status = 'shipped'
            else:
                # Default for 'sale' or other states
                mapped_status = 'confirmed'
                
            payload = {'status': mapped_status}
            self.api.put(f"/orders/{order.x_external_id}", json=payload)
            self._log_sync('mini.order', 'outbound', 'success', f"Pushed status {order.state}", order.x_external_id)
        except Exception as e:
            self._log_sync('mini.order', 'outbound', 'failed', str(e), order.x_external_id)

    # ─── HELPER ───────────────────────────────────────────────────────

    def _log_sync(self, model, direction, state, error_message='', ext_id=''):
        self.env['sync.log'].create({
            'name': f"{direction.title()} Sync - {model}",
            'model': model,
            'direction': direction,
            'state': state,
            'error_message': error_message,
            'external_id': ext_id,
        })
