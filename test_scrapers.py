"""
Test script to verify Zoopla and Rightmove scrapers are working correctly
"""
import asyncio
from scrapers.zoopla import scrape_zoopla_first_page
from scrapers.rightmove_url import get_final_rightmove_results_url
from scrapers.rightmove_scrape import scrape_rightmove_from_url
from utils.logger import logger

async def test_zoopla():
    """Test Zoopla scraper"""
    print("\n" + "="*60)
    print("TESTING ZOOPLA SCRAPER")
    print("="*60)
    
    try:
        # Test with London rentals
        location = "London"
        min_price = "1000"
        max_price = "2000"
        min_beds = "1"
        max_beds = "2"
        listing_type = "rent"
        
        print(f"\nTest Parameters:")
        print(f"  Location: {location}")
        print(f"  Price Range: £{min_price} - £{max_price}")
        print(f"  Bedrooms: {min_beds} - {max_beds}")
        print(f"  Type: {listing_type}")
        
        results, total_pages = await scrape_zoopla_first_page(
            location=location,
            min_price=min_price,
            max_price=max_price,
            min_beds=min_beds,
            max_beds=max_beds,
            listing_type=listing_type
        )
        
        print(f"\n✓ Zoopla Results:")
        print(f"  Total Pages: {total_pages}")
        print(f"  Listings Found: {len(results)}")
        
        if results:
            print(f"\n  First Listing Sample:")
            first = results[0]
            print(f"    Title: {first.get('title', 'N/A')[:60]}...")
            print(f"    Price: {first.get('price', 'N/A')}")
            print(f"    Address: {first.get('address', 'N/A')[:50]}...")
            print(f"    Specs: {first.get('specs', 'N/A')}")
            print(f"    Has Image: {'Yes' if first.get('image') else 'No'}")
            print(f"    URL: {first.get('url', 'N/A')[:60]}...")
            
            return True
        else:
            print("\n  ⚠ WARNING: No listings found!")
            return False
            
    except Exception as e:
        print(f"\n✗ Zoopla Test FAILED: {str(e)}")
        logger.error(f"Zoopla test error: {str(e)}", exc_info=True)
        return False

def test_rightmove():
    """Test Rightmove scraper"""
    print("\n" + "="*60)
    print("TESTING RIGHTMOVE SCRAPER")
    print("="*60)
    
    try:
        # Test with London sales
        location = "London"
        min_price = "200000"
        max_price = "400000"
        min_beds = "1"
        max_beds = "2"
        listing_type = "sale"
        
        print(f"\nTest Parameters:")
        print(f"  Location: {location}")
        print(f"  Price Range: £{min_price} - £{max_price}")
        print(f"  Bedrooms: {min_beds} - {max_beds}")
        print(f"  Type: {listing_type}")
        
        # First, generate URL
        url = get_final_rightmove_results_url(
            location=location,
            min_price=min_price,
            max_price=max_price,
            min_beds=min_beds,
            max_beds=max_beds,
            listing_type=listing_type
        )
        
        if not url:
            print("\n✗ URL Generation FAILED")
            return False
            
        print(f"\n  Generated URL: {url[:80]}...")
        
        # Now scrape
        results = scrape_rightmove_from_url(url, page=1)
        
        print(f"\n✓ Rightmove Results:")
        print(f"  Total Found: {results.get('total_found', 0)}")
        print(f"  Total Pages: {results.get('total_pages', 0)}")
        print(f"  Current Page: {results.get('current_page', 1)}")
        print(f"  Listings Returned: {len(results.get('listings', []))}")
        
        listings = results.get('listings', [])
        if listings:
            print(f"\n  First Listing Sample:")
            first = listings[0]
            print(f"    Title: {first.get('title', 'N/A')[:60]}...")
            print(f"    Price: {first.get('price', 'N/A')}")
            print(f"    Address: {first.get('address', 'N/A')[:50]}...")
            print(f"    Specs: {first.get('specs', 'N/A')}")
            print(f"    Has Image: {'Yes' if first.get('image') else 'No'}")
            print(f"    URL: {first.get('url', 'N/A')[:60]}...")
            
            return True
        else:
            print("\n  ⚠ WARNING: No listings found!")
            return False
            
    except Exception as e:
        print(f"\n✗ Rightmove Test FAILED: {str(e)}")
        logger.error(f"Rightmove test error: {str(e)}", exc_info=True)
        return False

async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SCRAPER VALIDATION TEST SUITE")
    print("="*60)
    
    # Test Zoopla
    zoopla_ok = await test_zoopla()
    
    # Test Rightmove
    rightmove_ok = test_rightmove()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"  Zoopla Scraper: {'✓ PASS' if zoopla_ok else '✗ FAIL'}")
    print(f"  Rightmove Scraper: {'✓ PASS' if rightmove_ok else '✗ FAIL'}")
    print("\n" + "="*60)
    
    if zoopla_ok and rightmove_ok:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED - Review output above")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
