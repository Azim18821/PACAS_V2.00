"""Test combined search functionality"""
import asyncio
from scraper_bot import ScraperBot
import json

async def test_combined():
    bot = ScraperBot()
    
    print("Testing Combined Search (Zoopla + Rightmove)")
    print("="*80)
    print("\nSearching: Manchester, For Sale, £200k-£400k, 2-3 beds")
    print("-"*80)
    
    results = await bot.scrape_combined(
        location="manchester",
        min_price="200000",
        max_price="400000",
        min_beds="2",
        max_beds="3",
        listing_type="sale",
        page=1,
        keywords=""
    )
    
    if results:
        print(f"\n✓ Combined Results:")
        print(f"  Total listings: {results.get('total_found', 0)}")
        print(f"  Total pages: {results.get('total_pages', 0)}")
        print(f"  Current page: {results.get('current_page', 0)}")
        print(f"  Has next page: {results.get('has_next_page', False)}")
        
        # Count by source
        sources = {}
        for listing in results.get('listings', []):
            source = listing.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        print(f"\n  Breakdown by source:")
        for source, count in sources.items():
            print(f"    {source}: {count} listings")
        
        # Show first few listings
        print(f"\n  First 3 listings:")
        for idx, listing in enumerate(results.get('listings', [])[:3], 1):
            print(f"\n  {idx}. {listing.get('source', 'Unknown')} - {listing.get('title', 'No title')[:60]}")
            print(f"     Price: {listing.get('price', 'N/A')}")
            print(f"     Address: {listing.get('address', 'N/A')[:60]}")
            print(f"     Image: {'Yes' if listing.get('image') else 'No'}")
            print(f"     URL: {listing.get('url', 'N/A')[:60]}...")
    else:
        print("\n✗ No results returned")
        
asyncio.run(test_combined())
