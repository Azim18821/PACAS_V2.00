import os
import asyncio
import random
import time
from datetime import datetime
from dotenv import load_dotenv
from scrapers.rightmove_url import get_final_rightmove_results_url
from scrapers.rightmove_scrape import scrape_rightmove_from_url
from utils.database import Database
from utils.logger import logger

# Load environment variables
load_dotenv()

class RightmoveBot:
    def __init__(self):
        self.db = Database()
        self.max_retries = 3
        self.retry_delay = 5
        self.max_pages = 247  # Maximum pages to scrape per combination
        self.max_consecutive_empty = 2  # Maximum consecutive empty pages before stopping
        self.radius = "0.0"  # Default radius for location search
        self.include_sold = True  # Include sold properties
        self.sort_by = "newest"  # Default sort order
        
        # Load ScraperAPI key
        self.scraperapi_key = os.getenv("SCRAPER_API_KEY")
        if not self.scraperapi_key:
            logger.error("[Rightmove Bot] No ScraperAPI key found in environment variables")
            raise ValueError("ScraperAPI key is required")
        
        logger.info("[Rightmove Bot] Initialized with ScraperAPI")

    def has_valid_listings(self, results):
        """Check if results contain any listings"""
        if not results or "listings" not in results:
            return False
        listings = results["listings"]
        if not listings:
            return False
        
        # Accept all listings from the scraper
        logger.info(f"[Rightmove Bot] Found {len(listings)} listings")
        return True

    def is_page_cached(self, location, min_price, max_price, min_beds, max_beds, listing_type, page):
        """Check if a page is already cached in the database and has valid listings"""
        cached_results = self.db.get_cached_results(
            site="Rightmove",
            location=location,
            min_price=min_price,
            max_price=max_price,
            min_beds=min_beds,
            max_beds=max_beds,
            keywords="",  # Empty string for keywords
            listing_type=listing_type,
            page_number=page
        )
        return cached_results is not None and self.has_valid_listings(cached_results)

    async def scrape_page(self, url, page):
        """Scrape a page using ScraperAPI"""
        try:
            logger.info(f"[Rightmove Bot] Scraping page {page}")
            results = scrape_rightmove_from_url(url, page=page)
            if results and self.has_valid_listings(results):
                logger.info(f"[Rightmove Bot] Successfully scraped page {page}")
                return results
            await asyncio.sleep(self.retry_delay)
        except Exception as e:
            logger.error(f"[Rightmove Bot] Error on page {page}: {str(e)}")
        
        logger.error(f"[Rightmove Bot] Failed to scrape page {page}")
        return None

    async def scrape_rightmove(self, location, min_price, max_price, min_beds, max_beds, listing_type, page=1):
        """Scrape Rightmove with improved error handling and validation"""
        try:
            # Check if page is already cached and has valid listings
            if self.is_page_cached(location, min_price, max_price, min_beds, max_beds, listing_type, page):
                logger.info(f"[Rightmove] Page {page} already cached for {location}")
                cached_results = self.db.get_cached_results(
                    site="Rightmove",
                    location=location,
                    min_price=min_price,
                    max_price=max_price,
                    min_beds=min_beds,
                    max_beds=max_beds,
                    keywords="",  # Empty string for keywords
                    listing_type=listing_type,
                    page_number=page
                )
                return cached_results

            url = get_final_rightmove_results_url(
                location=location,
                min_price=min_price,
                max_price=max_price,
                min_beds=min_beds,
                max_beds=max_beds,
                radius=self.radius,
                include_sold=self.include_sold,
                listing_type=listing_type,
                sort_by=self.sort_by,
                page=page
            )
            
            if not url:
                logger.error(f"[Rightmove] Failed to generate URL for {location}")
                return None

            # Add random delay between requests
            await asyncio.sleep(random.uniform(2, 4))
            
            # Try scraping with retries
            results = None
            for attempt in range(self.max_retries):
                results = await self.scrape_page(url, page)
                if results and self.has_valid_listings(results):
                    break
                await asyncio.sleep(self.retry_delay)
                logger.warning(f"[Rightmove Bot] Retry {attempt + 1}/{self.max_retries} for page {page}")
            
            if not results or not self.has_valid_listings(results):
                logger.warning(f"[Rightmove] No valid listings found for {location} on page {page}")
                return None

            # Check for "no results" message
            if results.get("no_results", False):
                logger.info(f"[Rightmove] No results found for {location} with current filters")
                return {
                    "listings": [],
                    "total_found": 0,
                    "total_pages": 0,
                    "current_page": page,
                    "has_next_page": False,
                    "is_complete": True,
                    "no_results": True
                }

            # Only cache results if they contain valid listings
            if self.has_valid_listings(results):
                self.db.cache_results(
                    site="Rightmove",
                    location=location,
                    min_price=min_price,
                    max_price=max_price,
                    min_beds=min_beds,
                    max_beds=max_beds,
                    keywords="",  # Empty string for keywords
                    listing_type=listing_type,
                    page_number=page,
                    results=results
                )
                logger.info(f"[Rightmove] Cached {len(results['listings'])} listings for page {page}")
            else:
                logger.warning(f"[Rightmove] Skipping cache for page {page} - no valid listings")
            
            return results
            
        except Exception as e:
            logger.error(f"[Rightmove ERROR] {str(e)}")
            return None

    async def scrape_all_pages(self, location, min_price, max_price, min_beds, max_beds, listing_type):
        """Scrape all pages for Rightmove with improved error handling"""
        logger.info(f"\n[Rightmove Bot] Starting scrape for {location} - {listing_type}")
        logger.info(f"Price range: £{min_price} - £{max_price}")
        logger.info(f"Bedrooms: {min_beds}-{max_beds}")
        
        consecutive_empty = 0
        total_listings = 0
        page = 1
        
        while page <= self.max_pages and consecutive_empty < self.max_consecutive_empty:
            results = await self.scrape_rightmove(
                location=location,
                min_price=min_price,
                max_price=max_price,
                min_beds=min_beds,
                max_beds=max_beds,
                listing_type=listing_type,
                page=page
            )
            
            if results and self.has_valid_listings(results):
                total_listings += len(results["listings"])
                consecutive_empty = 0
                logger.info(f"[Rightmove Bot] Total listings so far: {total_listings}")
                
                # Check if we've reached the last page
                if results.get("is_complete", False):
                    logger.info("[Rightmove Bot] Reached last page")
                    break
            else:
                consecutive_empty += 1
                logger.warning(f"[Rightmove Bot] Empty page {page}, consecutive empty: {consecutive_empty}")
            
            page += 1
        
        logger.info(f"[Rightmove Bot] Finished scraping {location}")
        logger.info(f"Total pages scraped: {page - 1}")
        logger.info(f"Total listings found: {total_listings}")
        return total_listings

    async def scrape_all_combinations(self):
        """Scrape all combinations of search parameters"""
        try:
            # Define search parameters
            locations = ["london"]
            
            # Sale parameters
            sale_min_prices = [None, 100000]
            sale_max_prices = [100000, None]
            sale_min_beds = [None, 1]
            sale_max_beds = [1, None]
            
            # Rental parameters
            rental_min_prices = [100, 500, 1000]
            rental_max_prices = [500, 1000, 20000]
            rental_min_beds = [None, 1]
            rental_max_beds = [1, None]
            
            listing_types = ["sale", "rent"]
            
            # Calculate total combinations
            sale_combinations = (
                len(locations) * len(sale_min_prices) * len(sale_max_prices) *
                len(sale_min_beds) * len(sale_max_beds)
            )
            rental_combinations = (
                len(locations) * len(rental_min_prices) * len(rental_max_prices) *
                len(rental_min_beds) * len(rental_max_beds)
            )
            total_combinations = sale_combinations + rental_combinations
            
            logger.info(f"[Rightmove Bot] Total combinations to scrape: {total_combinations}")
            
            combination_count = 0
            for location in locations:
                # Handle sale listings
                for listing_type in ["sale"]:
                    for min_price in sale_min_prices:
                        for max_price in sale_max_prices:
                            for min_bed in sale_min_beds:
                                for max_bed in sale_max_beds:
                                    combination_count += 1
                                    logger.info(f"\n[Rightmove Bot] Processing sale combination {combination_count}/{total_combinations}")
                                    logger.info(f"Price range: £{min_price or 0} - £{max_price or 'unlimited'}")
                                    logger.info(f"Bedrooms: {min_bed or 'any'}-{max_bed or 'any'}")
                                    
                                    await self.scrape_all_pages(
                                        location=location,
                                        min_price=min_price,
                                        max_price=max_price,
                                        min_beds=min_bed,
                                        max_beds=max_bed,
                                        listing_type=listing_type
                                    )
                
                # Handle rental listings
                for listing_type in ["rent"]:
                    for min_price in rental_min_prices:
                        for max_price in rental_max_prices:
                            for min_bed in rental_min_beds:
                                for max_bed in rental_max_beds:
                                    combination_count += 1
                                    logger.info(f"\n[Rightmove Bot] Processing rental combination {combination_count}/{total_combinations}")
                                    logger.info(f"Price range: £{min_price} - £{max_price}")
                                    logger.info(f"Bedrooms: {min_bed or 'any'}-{max_bed or 'any'}")
                                    
                                    await self.scrape_all_pages(
                                        location=location,
                                        min_price=min_price,
                                        max_price=max_price,
                                        min_beds=min_bed,
                                        max_beds=max_bed,
                                        listing_type=listing_type
                                    )
            
            logger.info("[Rightmove Bot] Finished scraping all combinations")
            
        except Exception as e:
            logger.error(f"[Rightmove Bot] Error in scrape_all_combinations: {str(e)}")

async def main():
    bot = RightmoveBot()
    await bot.scrape_all_combinations()

if __name__ == "__main__":
    asyncio.run(main()) 