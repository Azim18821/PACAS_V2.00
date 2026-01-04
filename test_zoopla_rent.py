"""
Test Zoopla rent search directly
"""
import asyncio
from scrapers.zoopla import scrape_zoopla_first_page

async def test_zoopla_rent():
    print("Testing Zoopla Rent Search...")
    print("=" * 60)
    
    try:
        results, total_pages = await scrape_zoopla_first_page(
            location="Manchester",
            min_price="500",
            max_price="2000",
            min_beds=2,
            max_beds=3,
            keywords="",
            listing_type="rent",
            page_number=1
        )
        
        print(f"\n[OK] Zoopla Rent Results:")
        print(f"  Total listings: {len(results) if results else 0}")
        print(f"  Total pages: {total_pages}")
        
        if results and len(results) > 0:
            print(f"\n  First 3 listings:")
            for i, listing in enumerate(results[:3], 1):
                print(f"\n  {i}. {listing.get('title', 'No title')}")
                print(f"     Price: {listing.get('price', 'N/A')}")
                print(f"     Address: {listing.get('address', 'N/A')}")
                print(f"     URL: {listing.get('url', 'N/A')[:80]}...")
        else:
            print("\n  [ERROR] No Zoopla rent listings found!")
            print("  This might be why combined search only shows Rightmove results")
    except Exception as e:
        print(f"\n  [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_zoopla_rent())
