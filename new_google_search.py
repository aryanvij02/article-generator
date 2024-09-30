import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

def google_search(url, query):
    url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID}&q=site:{url}+{query}"
    response = requests.get(url)
    return response.json()

# Example usage
results = google_search("https://www.myaifrontdesk.com/blogs", "AI phone call")
items = results.get('items', [])
print(f"URL: {items[0]['link']}")
