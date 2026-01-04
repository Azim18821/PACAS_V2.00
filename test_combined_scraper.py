"""
Test script to verify the combined scraper (Zoopla + Rightmove)
"""
import asyncio
from scraper_bot import ScraperBot
from utils.logger import logger

async def test_combined_scraper():
    """Test combined scraper with both Zoopla and Rightmove"""
    print("\n" + "="*60)
    print("TESTING COMBINED SCRAPER (ZOOPLA + RIGHTMOVE)")
    print("="*60)
    
    try:
        # Test parameters
        location = "London"
        min_price = "300000"
        max_price = "400000"
        min_beds = 1
        max_beds = 2
        listing_type = "sale"
        page = 1
        
        print(f"\nTest Parameters:")
        print(f"  Location: {location}")
        print(f"  Price Range: £{min_price} - £{max_price}")
        print(f"  Bedrooms: {min_beds} - {max_beds}")
        print(f"  Type: {listing_type}")
        print(f"  Page: {page}")
        
        # Initialize scraper bot
        scraper_bot = ScraperBot()
        print("\n✓ ScraperBot initialized")
        
        # Run combined scrape
        print("\nStarting combined scrape...")
        results = await scraper_bot.scrape_combined(
            location=location,
            min_price=min_price,
            max_price=max_price,
            min_beds=min_beds,
            max_beds=max_beds,
            listing_type=listing_type,
            page=page,
            keywords=""
        )
        
        print("\n" + "="*60)
        print("COMBINED SCRAPER RESULTS")
        print("="*60)
        
        # Check if results are valid
        if not results or not isinstance(results, dict):
            print("\n✗ FAILED: Invalid results structure")
            return False
        
        # Display overall statistics
        print(f"\n📊 Overall Statistics:")
        print(f"  Total Unique Listings: {results.get('total_found', 0)}")
        print(f"  Total Pages: {results.get('total_pages', 0)}")
        print(f"  Current Page: {results.get('current_page', 1)}")
        print(f"  Has Next Page: {results.get('has_next_page', False)}")
        
        # Display site-specific stats
        if 'site_stats' in results:
            print(f"\n📈 Site-Specific Statistics:")
            stats = results['site_stats']
            
            if 'zoopla' in stats:
                zoopla = stats['zoopla']
                print(f"\n  Zoopla:")
                print(f"    Listings: {zoopla.get('listings', 0)}")
                print(f"    Total Pages: {zoopla.get('total_pages', 0)}")
                print(f"    Source: {zoopla.get('source', 'N/A')}")
            
            if 'rightmove' in stats:
                rightmove = stats['rightmove']
                print(f"\n  Rightmove:")
                print(f"    Listings: {rightmove.get('listings', 0)}")
                print(f"    Total Pages: {rightmove.get('total_pages', 0)}")
                print(f"    Source: {rightmove.get('source', 'N/A')}")
        
        # Display listings
        listings = results.get('listings', [])
        print(f"\n📋 Listings Breakdown:")
        print(f"  Total Listings Retrieved: {len(listings)}")
        
        if listings:
            # Count by source
            zoopla_count = sum(1 for l in listings if l.get('source') == 'Zoopla')
            rightmove_count = sum(1 for l in listings if l.get('source') == 'Rightmove')
            
            print(f"  Zoopla Listings: {zoopla_count}")
            print(f"  Rightmove Listings: {rightmove_count}")
            
            # Show first listing from each source
            print(f"\n📄 Sample Listings:")
            
            zoopla_listing = next((l for l in listings if l.get('source') == 'Zoopla'), None)
            if zoopla_listing:
                print(f"\n  First Zoopla Listing:")
                print(f"    Title: {zoopla_listing.get('title', 'N/A')[:60]}...")
                print(f"    Price: {zoopla_listing.get('price', 'N/A')}")
                print(f"    Address: {zoopla_listing.get('address', 'N/A')[:50]}...")
                print(f"    Specs: {zoopla_listing.get('specs', 'N/A')}")
                print(f"    Has Image: {'Yes' if zoopla_listing.get('image') else 'No'}")
                print(f"    Source: {zoopla_listing.get('source', 'N/A')}")
            
            rightmove_listing = next((l for l in listings if l.get('source') == 'Rightmove'), None)
            if rightmove_listing:
                print(f"\n  First Rightmove Listing:")
                print(f"    Title: {rightmove_listing.get('title', 'N/A')[:60]}...")
                print(f"    Price: {rightmove_listing.get('price', 'N/A')}")
                print(f"    Address: {rightmove_listing.get('address', 'N/A')[:50]}...")
                print(f"    Specs: {rightmove_listing.get('specs', 'N/A')}")
                print(f"    Has Image: {'Yes' if rightmove_listing.get('image') else 'No'}")
                print(f"    Source: {rightmove_listing.get('source', 'N/A')}")
            
            # Verify deduplication
            unique_ids = set()
            duplicates = 0
            for listing in listings:
                listing_id = listing.get('id')
                if listing_id:
                    if listing_id in unique_ids:
                        duplicates += 1
                    unique_ids.add(listing_id)
            
            print(f"\n🔍 Deduplication Check:")
            print(f"  Unique IDs: {len(unique_ids)}")
            print(f"  Duplicates Found: {duplicates}")
            
            if duplicates > 0:
                print(f"  ⚠ WARNING: {duplicates} duplicate listings detected!")
            else:
                print(f"  ✓ No duplicates found")
            
            return True
        else:
            print("\n  ⚠ WARNING: No listings retrieved!")
            return False
            
    except Exception as e:
        print(f"\n✗ Combined Scraper Test FAILED: {str(e)}")
        logger.error(f"Combined scraper test error: {str(e)}", exc_info=True)
        return False

async def main():
    """Run the test"""
    print("\n" + "="*60)
    print("COMBINED SCRAPER VALIDATION TEST")
    print("="*60)
    
    result = await test_combined_scraper()
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"  Combined Scraper: {'✓ PASS' if result else '✗ FAIL'}")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
