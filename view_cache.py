import sqlite3
from datetime import datetime
import json

def view_cache():
    conn = sqlite3.connect('listings.db')
    cursor = conn.cursor()
    
    # Get all cached results
    cursor.execute('''
        SELECT site, location, min_price, max_price, min_beds, max_beds, 
               keywords, listing_type, page_number, created_at, results 
        FROM listings
        ORDER BY created_at DESC
    ''')
    
    results = cursor.fetchall()
    
    print(f"\nFound {len(results)} cached pages:\n")
    
    # Track unique pages per search combination
    search_combinations = {}
    
    for row in results:
        site, location, min_price, max_price, min_beds, max_beds, \
        keywords, listing_type, page_number, created_at, results_json = row
        
        # Create a key for this search combination
        combo_key = f"{site}_{location}_{min_price}_{max_price}_{min_beds}_{max_beds}_{listing_type}"
        if combo_key not in search_combinations:
            search_combinations[combo_key] = {
                'pages': set(),
                'total_listings': 0,
                'details': {
                    'site': site,
                    'location': location,
                    'price_range': f"{min_price or 'Any'} - {max_price or 'Any'}",
                    'beds': f"{min_beds or 'Any'} - {max_beds or 'Any'}",
                    'listing_type': listing_type,
                    'last_updated': created_at
                }
            }
        
        try:
            data = json.loads(results_json)
            listings = data.get('listings', [])
            search_combinations[combo_key]['pages'].add(page_number)
            search_combinations[combo_key]['total_listings'] += len(listings)
        except json.JSONDecodeError:
            print(f"Error decoding JSON for {site} - {location} page {page_number}")
    
    # Print summary for each search combination
    for combo_key, info in search_combinations.items():
        print(f"\nSite: {info['details']['site']}")
        print(f"Location: {info['details']['location']}")
        print(f"Price Range: {info['details']['price_range']}")
        print(f"Beds: {info['details']['beds']}")
        print(f"Listing Type: {info['details']['listing_type']}")
        print(f"Pages Cached: {sorted(list(info['pages']))}")
        print(f"Total Listings: {info['total_listings']}")
        print(f"Last Updated: {info['details']['last_updated']}")
        print("-" * 50)
    
    conn.close()

if __name__ == "__main__":
    view_cache() 