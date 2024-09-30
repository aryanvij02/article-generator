from googlesearch import search
import requests
import logging
import os
from dotenv import load_dotenv
import urllib.parse
import re
load_dotenv()

GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

def internal_linking_search(url, search_query):
    encoded_url = urllib.parse.quote(url)
    encoded_query = urllib.parse.quote(search_query)
    api_url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}&q=site:{encoded_url}+{encoded_query}"
    response = requests.get(api_url)
    results = response.json()
    items = results.get('items', [])
    if len(items) > 0:
        return f'href="{items[0]["link"]}"'
    else:
        # If no internal results, try external linking
        logging.info(f"No internal results found for '{search_query}'. Trying external search.")
        return external_linking_search(search_query)

def external_linking_search(search_query):
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}&q={search_query}"
    response = requests.get(url)
    results = response.json()
    items = results.get('items', [])
    
    reddit_pattern = re.compile(r'https?://(?:www\.)?reddit\.com')
    
    for item in items:
        first_url = item['link']
        if not reddit_pattern.match(first_url):
            return f'href="{first_url}"'
    
    return 'href="#"'

if __name__ == "__main__":
    print(internal_linking_search("https://www.myaifrontdesk.com/blogs", "SEO Strategies for AI Phone Receptionist Affiliate Marketers"))
