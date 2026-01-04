"""Find OpenRent property listings"""
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

print(f"Fetching: {search_url}\n")

proxy_url = get_proxy_url(search_url)
response = requests.get(proxy_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)

soup = BeautifulSoup(response.text, 'html.parser')

print("="*80)
print("SEARCHING FOR PROPERTY LISTINGS")
print("="*80)

# Try different selectors
selectors = [
    "a.pli",
    ".pli",
    "div.listing",
    ".listing-item",
    "article",
    "[data-testid='listing']",
    ".property-card",
    "a[href*='/property-to-rent']"
]

for selector in selectors:
    results = soup.select(selector)
    print(f"\n'{selector}': Found {len(results)} elements")
    if results and len(results) > 0:
        print(f"  First element tag: {results[0].name}")
        print(f"  First element classes: {results[0].get('class', [])}")

# Check for images
print("\n" + "="*80)
print("SEARCHING FOR IMAGES")
print("="*80)
images = soup.find_all("img")
print(f"Total images found: {len(images)}")
for idx, img in enumerate(images[:5]):
    print(f"\n{idx+1}. Image:")
    print(f"   src: {img.get('src', 'N/A')[:80]}")
    print(f"   data-src: {img.get('data-src', 'N/A')[:80]}")
    print(f"   alt: {img.get('alt', 'N/A')[:80]}")
    print(f"   classes: {img.get('class', [])}")

# Look for price elements
print("\n" + "="*80)
print("SEARCHING FOR PRICES")
print("="*80)
price_indicators = ["£", "pcm", "pw"]
for indicator in price_indicators:
    elements = soup.find_all(string=lambda text: indicator in text if text else False)
    print(f"\nElements containing '{indicator}': {len(elements)}")
    if elements:
        for elem in elements[:3]:
            parent = elem.parent if elem else None
            print(f"  - Text: {str(elem)[:60]}")
            print(f"    Parent: {parent.name if parent else 'N/A'}, classes: {parent.get('class', []) if parent else 'N/A'}")

# Save HTML for inspection
with open('openrent_debug.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())
print("\n✓ Full HTML saved to openrent_debug.html")
