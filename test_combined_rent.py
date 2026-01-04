"""
Test combined rent search
"""
import asyncio
from scraper_bot import ScraperBot

async def test_combined_rent():
    print("Testing Combined Rent Search...")
    print("=" * 60)
    
    bot = ScraperBot()
    
    # Test parameters for rent
    results = await bot.scrape_combined(
        location="Manchester",
        min_price="500",
        max_price="2000",
        min_beds=2,
        max_beds=3,
        listing_type="rent",
        page=1,
        keywords=""
    )
    
    print(f"\n✓ Combined Results:")
    print(f"  Total listings: {results.get('total_found', 0)}")
    print(f"  Total pages: {results.get('total_pages', 0)}")
    print(f"  Current page: {results.get('current_page', 1)}")
    print(f"  Has next page: {results.get('has_next_page', False)}")
    
    if 'listings' in results and results['listings']:
        print(f"\n  First 3 listings:")
        for i, listing in enumerate(results['listings'][:3], 1):
            print(f"\n  {i}. {listing.get('source', 'Unknown')} - {listing.get('title', 'No title')}")
            print(f"     Price: {listing.get('price', 'N/A')}")
            print(f"     Address: {listing.get('address', 'N/A')}")
            print(f"     URL: {listing.get('url', 'N/A')[:80]}...")
    else:
        print("\n  ❌ No listings found!")
        print(f"  Full results: {results}")

if __name__ == "__main__":
    asyncio.run(test_combined_rent())
