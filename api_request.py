import logging
import requests
from typing import List, Dict, Optional

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class APIError(Exception):
    """Custom exception for API-related errors."""
    pass

def make_api_request(url: str, method: str = 'GET', headers: Dict = None, params: Dict = None, json: Dict = None) -> Dict:
    """Make an API request and handle common errors."""
    try:
        # logging.info(f"Making {method} request to {url}")
        # logging.debug(f"Request headers: {headers}")
        # logging.debug(f"Request params: {params}")
        # logging.debug(f"Request payload: {json}")
        response = requests.request(method, url, headers=headers, params=params, json=json)
        # logging.info(f"Response status code: {response.status_code}")
        # logging.debug(f"Response headers: {response.headers}")
        # logging.debug(f"Response content: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        logging.error(f"Response content: {response.text if 'response' in locals() else 'No response'}")
        raise APIError(f"API request failed: {e}")