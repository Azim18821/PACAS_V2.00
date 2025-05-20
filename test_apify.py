
from scrapers.openrent import scrape_openrent
import json

def test_openrent():
    # Test parameters
    location = "manchester"
    min_price = "500"
    max_price = "2000" 
    min_beds = "1"
    
    print("Testing OpenRent scraper...")
    results = scrape_openrent(
        location=location,
        min_price=min_price,
        max_price=max_price,
        min_beds=min_beds
    )
    
    # Print results in a readable format
    if results and len(results['listings']) > 0:
        print(f"\nFound {len(results['listings'])} listings")
        print(f"Total pages: {results['total_pages']}")
        print("\nFirst listing details:")
        first = results['listings'][0]
        print(json.dumps(first, indent=2))
    else:
        print("No results found")

if __name__ == "__main__":
    test_openrent()
