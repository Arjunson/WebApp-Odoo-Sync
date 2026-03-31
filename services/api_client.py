import requests
import logging
from requests.exceptions import RequestException

_logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, env):
        self.env = env
        config = self.env['sync.config'].get_config()
        self.base_url = config.api_base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {config.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}{endpoint}"
        retries = 3
        for attempt in range(retries):
            try:
                response = requests.request(method, url, headers=self.headers, timeout=10, **kwargs)
                response.raise_for_status()
                if response.status_code == 204:
                    return {}
                return response.json()
            except RequestException as e:
                _logger.warning(f"API {method} {url} failed. Attempt {attempt + 1}/{retries}. Error: {e}")
                if attempt == retries - 1:
                    raise Exception(f"API Error: {str(e)}")

    def get(self, endpoint, params=None):
        return self._request('GET', endpoint, params=params)

    def post(self, endpoint, json=None):
        return self._request('POST', endpoint, json=json)

    def put(self, endpoint, json=None):
        return self._request('PUT', endpoint, json=json)
