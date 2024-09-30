import logging
import requests
from api_request import make_api_request, APIError
import time
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
PEXELS_BASE_URL = 'https://api.pexels.com/v1/search'

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def search_images(query: str, num_images: int = 1):
    headers = {
        'Authorization': PEXELS_API_KEY,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    params = {'query': query, 'per_page': num_images, 'orientation': 'landscape'}
    
    for attempt in range(MAX_RETRIES):
        try:
            logging.debug(f"Searching for images with query: {query} (Attempt {attempt + 1})")
            data = make_api_request(PEXELS_BASE_URL, headers=headers, params=params)
            urls = [photo['src']['large'] for photo in data['photos']]
            logging.info(f"Found {len(urls)} images for query: {query}")
            logging.debug(f"Image URLs: {urls}")
            return urls
        except APIError as e:
            logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                logging.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Failed to fetch images for query: {query} after {MAX_RETRIES} attempts.")
    
    return []

def verify_image_url(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        is_valid = response.status_code == 200 and response.headers.get('content-type', '').startswith('image/')
        logging.info(f"Verifying image URL: {url} - Valid: {is_valid}")
        return is_valid
    except requests.RequestException as e:
        logging.error(f"Error verifying image URL {url}: {e}")
        return False

if __name__ == "__main__":
    # Test the search_images function
    query = "AI SEO integration"
    num_images = 1
    image_urls = search_images(query, num_images)
    
    print(f"Search results for '{query}':")
    for i, url in enumerate(image_urls, 1):
        print(f"{i}. {url}")
        is_valid = verify_image_url(url)
        print(f"   Valid: {is_valid}")
        print()

    # Test with an invalid query
    invalid_query = "thisisaninvalidqueryfortest123456789"
    invalid_results = search_images(invalid_query)
    print(f"\nSearch results for invalid query '{invalid_query}':")
    print(f"Number of results: {len(invalid_results)}")
