"""Check OpenRent HTML structure"""
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")

def get_proxy_url(url):
    return f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"

# Build URL
params = {
    'term': 'manchester',
    'sortType': 'newestFirst',
    'prices_min': '500',
    'prices_max': '1500',
    'bedrooms_min': '2'
}
base_url = "https://www.openrent.co.uk/properties-to-rent"
search_url = f"{base_url}?{urlencode(params)}"

proxy_url = get_proxy_url(search_url)
response = requests.get(proxy_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)

soup = BeautifulSoup(response.text, 'html.parser')

# Find property cards
property_cards = soup.select("a.pli")
print(f"Found {len(property_cards)} property cards\n")

if property_cards:
    card = property_cards[0]
    print("="*80)
    print("FIRST CARD HTML:")
    print("="*80)
    print(card.prettify()[:2000])
    print("\n" + "="*80)
    print("CHECKING SELECTORS:")
    print("="*80)
    
    # Check all possible selectors
    print(f"\n1. .banda: {card.select_one('.banda')}")
    print(f"2. .price: {card.select_one('.price')}")
    print(f"3. .description: {card.select_one('.description')}")
    print(f"4. img.propertyPic: {card.select_one('img.propertyPic')}")
    
    # Try alternative selectors
    print(f"\n5. All classes in card:")
    for elem in card.find_all(class_=True):
        print(f"   - {elem.name}: {elem.get('class')}")
    
    print(f"\n6. All text in card (first 500 chars):")
    print(card.get_text()[:500])
