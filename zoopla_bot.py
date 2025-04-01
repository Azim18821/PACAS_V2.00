import os
import asyncio
import random
import time
from datetime import datetime
from dotenv import load_dotenv
from scrapers.zoopla import scrape_zoopla_first_page, scrape_zoopla_page
from scrapers.proxy_rotator import ProxyRotator
from utils.database import Database
from utils.logger import logger

# Load environment variables
load_dotenv()

class ZooplaBot:
    def __init__(self):
        self.db = Database()
        self.proxy_rotator = ProxyRotator()
        self.max_retries = 3
        self.retry_delay = 5
        self.max_pages = 247  # Maximum pages to scrape per combination
        self.max_consecutive_empty = 2  # Maximum consecutive empty pages before stopping

    def get_proxy_url(self, url):
        """Get the proxy URL using the proxy rotator"""
        return self.proxy_rotator.get_proxy_url(url)

    def has_valid_listings(self, results):
        """Check if results contain valid listings"""
        if not results or "listings" not in results:
            return False
        listings = results["listings"]
        if not listings:
            return False
        # Check if at least one listing has required fields
        return any(
            listing.get("title") and 
            listing.get("price") and 
            listing.get("link")  # Changed to match scraper output
            for listing in listings
        )

    def is_page_cached(self, location, min_price, max_price, min_beds, max_beds, listing_type, page, keywords=""):
        """Check if a page is already cached in the database"""
        cached_results = self.db.get_cached_results(
            site="Zoopla",
            location=location,
            min_price=min_price,
            max_price=max_price,
            min_beds=min_beds,
            max_beds=max_beds,
            keywords=keywords,
            listing_type=listing_type,
            page_number=page
        )
        return cached_results is not None and self.has_valid_listings(cached_results)

    async def scrape_zoopla(self, location, min_price, max_price, min_beds, max_beds, listing_type, page=1, keywords=""):
        """Scrape Zoopla with improved error handling and validation"""
        try:
            # Check if page is already cached
            if self.is_page_cached(location, min_price, max_price, min_beds, max_beds, listing_type, page, keywords):
                logger.info(f"[Zoopla] Page {page} already cached for {location}")
                return self.db.get_cached_results(
                    site="Zoopla",
                    location=location,
                    min_price=min_price,
                    max_price=max_price,
                    min_beds=min_beds,
                    max_beds=max_beds,
                    keywords=keywords,
                    listing_type=listing_type,
                    page_number=page
                )

            # Add random delay between requests
            await asyncio.sleep(random.uniform(2, 4))
            
            if page == 1:
                results, total_pages = await scrape_zoopla_first_page(
                    location=location,
                    min_price=min_price,
                    max_price=max_price,
                    min_beds=min_beds,
                    max_beds=max_beds,
                    keywords=keywords,
                    listing_type=listing_type,
                    page_number=page
                )
            else:
                results = await scrape_zoopla_page(
                    location=location,
                    min_price=min_price,
                    max_price=max_price,
                    min_beds=min_beds,
                    max_beds=max_beds,
                    keywords=keywords,
                    listing_type=listing_type,
                    page_num=page
                )
                total_pages = page  # We don't know total pages for subsequent pages

            if not results:
                logger.warning(f"[Zoopla] No valid listings found for {location} on page {page}")
                return None

            # Create structured results object
            structured_results = {
                "listings": results,
                "total_found": len(results) * total_pages if total_pages > 0 else len(results),
                "total_pages": total_pages,
                "current_page": page,
                "has_next_page": page < total_pages,
                "is_complete": page >= total_pages
            }

            # Cache results if valid
            self.db.cache_results(
                site="Zoopla",
                location=location,
                min_price=min_price,
                max_price=max_price,
                min_beds=min_beds,
                max_beds=max_beds,
                keywords=keywords,
                listing_type=listing_type,
                page_number=page,
                results=structured_results
            )
            
            return structured_results

        except Exception as e:
            logger.error(f"[Zoopla ERROR] {str(e)}")
            return None

    async def scrape_all_pages(self, location, min_price, max_price, min_beds, max_beds, listing_type, keywords=""):
        """Scrape all pages for Zoopla with improved error handling"""
        logger.info(f"\n[Zoopla Bot] Starting scrape for {location} - {listing_type}")
        logger.info(f"Price range: £{min_price} - £{max_price}")
        logger.info(f"Bedrooms: {min_beds}-{max_beds}")
        if keywords:
            logger.info(f"Keywords: {keywords}")
        
        consecutive_empty = 0
        page = 1
        
        while page <= self.max_pages:
            logger.info(f"\n[Zoopla Bot] Scraping page {page}")
            
            results = await self.scrape_zoopla(
                location, min_price, max_price, min_beds, max_beds, listing_type, page, keywords
            )
            
            if not results:
                consecutive_empty += 1
                logger.warning(f"[Zoopla Bot] No results found on page {page} ({consecutive_empty}/{self.max_consecutive_empty})")
                
                if consecutive_empty >= self.max_consecutive_empty:
                    logger.info("[Zoopla Bot] Stopping due to consecutive empty pages")
                    break
            else:
                consecutive_empty = 0
                
                # Check if we've reached the last page
                if results.get("is_complete"):
                    logger.info("[Zoopla Bot] Reached last page")
                    break
            
            # Add longer delay between pages
            await asyncio.sleep(random.uniform(5, 8))
            page += 1

    async def scrape_all_combinations(self):
        """Scrape all combinations of parameters"""
        locations = ["london", "manchester", "birmingham", "leeds"]
        listing_types = ["sale", "rent"]
        price_ranges = [
            ("0", "100000"),
            ("100000", "200000"),
            ("200000", "300000"),
            ("300000", "400000"),
            ("400000", "500000"),
            ("500000", "1000000")
        ]
        bed_ranges = [
            ("0", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5")
        ]
        keywords = ["garden", "garage", "parking"]  # Example keywords to search for

        total_combinations = len(locations) * len(listing_types) * len(price_ranges) * len(bed_ranges) * len(keywords)
        logger.info(f"\n[Zoopla Bot] Starting scrape of {total_combinations} combinations")
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        for location in locations:
            for listing_type in listing_types:
                for min_price, max_price in price_ranges:
                    for min_beds, max_beds in bed_ranges:
                        for keyword in keywords:
                            logger.info(f"\n[Zoopla Bot] Processing combination:")
                            logger.info(f"Location: {location}")
                            logger.info(f"Type: {listing_type}")
                            logger.info(f"Price: £{min_price} - £{max_price}")
                            logger.info(f"Beds: {min_beds}-{max_beds}")
                            logger.info(f"Keyword: {keyword}")
                            
                            await self.scrape_all_pages(
                                location=location,
                                min_price=min_price,
                                max_price=max_price,
                                min_beds=min_beds,
                                max_beds=max_beds,
                                listing_type=listing_type,
                                keywords=keyword
                            )

        logger.info(f"\n[Zoopla Bot] Finished scraping all combinations")
        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    bot = ZooplaBot()
    await bot.scrape_all_combinations()

if __name__ == "__main__":
    asyncio.run(main()) 