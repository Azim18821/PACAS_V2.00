"""Test OpenRent scraper"""
from scrapers.openrent import scrape_openrent
import json

print("Testing OpenRent scraper...")
print("="*80)

results = scrape_openrent("manchester", min_price="500", max_price="1500", min_beds="2")

print(f"\nType of results: {type(results)}")
print(f"Keys in results: {results.keys() if isinstance(results, dict) else 'Not a dict'}")
print(f"\nTotal listings: {len(results.get('listings', [])) if isinstance(results, dict) else len(results)}")
print(f"Total found: {results.get('total_found', 'N/A')}")
print(f"Total pages: {results.get('total_pages', 'N/A')}")

if isinstance(results, dict) and results.get('listings'):
    print(f"\nFirst listing:")
    print(json.dumps(results['listings'][0], indent=2))
