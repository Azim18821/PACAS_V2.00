import os
import asyncio
import aiohttp
import random
import time
from datetime import datetime
from dotenv import load_dotenv
from scrapers.rightmove_url import get_final_rightmove_results_url
from scrapers.rightmove_scrape import scrape_rightmove_from_url
from scrapers.zoopla import scrape_zoopla_first_page, scrape_zoopla_page
from utils.database import Database
from utils.logger import logger

# Load environment variables
load_dotenv()

def get_proxy_url(url):
    """Get the proxy URL for scraping"""
    scraper_api_key = os.getenv("SCRAPER_API_KEY")
    if not scraper_api_key:
        logger.error("[Scraper Bot] No SCRAPER_API_KEY found in environment variables")
        return url

    proxy_url = f"http://api.scraperapi.com?api_key={scraper_api_key}&url={url}"
    return proxy_url

class ScraperBot:
    def __init__(self):
        self.db = Database()
        self.max_retries = 3
        self.retry_delay = 5
        self.max_pages = 247  # Maximum pages to scrape per combination
        self.max_consecutive_empty = 2  # Maximum consecutive empty pages before stopping
        self.radius = "0.0"  # Default radius for location search
        self.include_sold = True  # Include sold properties for Rightmove
        self.sort_by = "newest"  # Default sort order

    def deduplicate_results(self, listings):
        """Remove duplicate listings based on URL"""
        seen_urls = set()
        unique_listings = []

        for listing in listings:
            url = listing.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_listings.append(listing)

        logger.info(f"Deduplicated {len(listings)} listings to {len(unique_listings)} unique listings")
        return unique_listings

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
            listing.get("link")
            for listing in listings
        )

    async def scrape_rightmove(self, location, min_price, max_price, min_beds, max_beds, listing_type, page=1, keywords=""):
        """Scrape Rightmove with improved error handling and validation"""
        try:
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

            results = scrape_rightmove_from_url(url, page=page)

            if not self.has_valid_listings(results):
                logger.warning(f"[Rightmove] No valid listings found for {location} on page {page}")
                return None

            # Filter by keywords if provided
            if keywords:
                filtered_listings = []
                for listing in results["listings"]:
                    text_to_search = " ".join([
                        listing.get("title", ""),
                        listing.get("price", ""),
                        listing.get("address", ""),
                        listing.get("desc", "")
                    ]).lower()
                    if keywords.lower() in text_to_search:
                        filtered_listings.append(listing)
                results["listings"] = filtered_listings

            # Cache results if valid
            self.db.cache_results(
                site="Rightmove",
                location=location,
                min_price=min_price,
                max_price=max_price,
                min_beds=min_beds,
                max_beds=max_beds,
                keywords=keywords,
                listing_type=listing_type,
                page_number=page,
                results=results
            )

            return results

        except Exception as e:
            logger.error(f"[Rightmove ERROR] {str(e)}")
            return None

    async def scrape_zoopla(self, location, min_price, max_price, min_beds, max_beds, listing_type, page=1, keywords=""):
        """Scrape Zoopla with improved error handling and validation"""
        try:
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
        """Scrape all pages for both sites with improved error handling"""
        logger.info(f"\n[Scraper Bot] Starting scrape for {location} - {listing_type}")
        logger.info(f"Price range: £{min_price} - £{max_price}")
        logger.info(f"Bedrooms: {min_beds}-{max_beds}")
        if keywords:
            logger.info(f"Keywords: {keywords}")

        consecutive_empty = 0
        page = 1

        while page <= self.max_pages:
            logger.info(f"\n[Scraper Bot] Scraping page {page}")

            # Scrape both sites concurrently
            rightmove_task = self.scrape_rightmove(
                location, min_price, max_price, min_beds, max_beds, listing_type, page, keywords
            )
            zoopla_task = self.scrape_zoopla(
                location, min_price, max_price, min_beds, max_beds, listing_type, page, keywords
            )

            rightmove_results, zoopla_results = await asyncio.gather(
                rightmove_task, zoopla_task, return_exceptions=True
            )

            # Check if both sites returned no results
            if not rightmove_results and not zoopla_results:
                consecutive_empty += 1
                logger.warning(f"[Scraper Bot] No results found on page {page} ({consecutive_empty}/{self.max_consecutive_empty})")

                if consecutive_empty >= self.max_consecutive_empty:
                    logger.info("[Scraper Bot] Stopping due to consecutive empty pages")
                    break
            else:
                consecutive_empty = 0

                # Check if we've reached the last page for both sites
                if (rightmove_results and rightmove_results.get("is_complete")) and \
                   (zoopla_results and zoopla_results.get("is_complete")):
                    logger.info("[Scraper Bot] Reached last page for both sites")
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
        logger.info(f"\n[Scraper Bot] Starting scrape of {total_combinations} combinations")
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        for location in locations:
            for listing_type in listing_types:
                for min_price, max_price in price_ranges:
                    for min_beds, max_beds in bed_ranges:
                        for keyword in keywords:
                            logger.info(f"\n[Scraper Bot] Processing combination:")
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

        logger.info(f"\n[Scraper Bot] Finished scraping all combinations")
        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    async def scrape_combined(self, location, min_price, max_price, min_beds, max_beds, listing_type, page=1, keywords=""):
        """Scrape both sites concurrently and return combined, deduplicated results"""
        try:
            logger.info(f"\n[Scraper Bot] Starting combined scrape for {location} - {listing_type}")
            logger.info(f"Price range: £{min_price} - £{max_price}")
            logger.info(f"Bedrooms: {min_beds}-{max_beds}")
            if keywords:
                logger.info(f"Keywords: {keywords}")

            # Create Rightmove URL
            rightmove_url = get_final_rightmove_results_url(
                location=location,
                min_price=min_price,
                max_price=max_price,
                min_beds=min_beds,
                max_beds=max_beds,
                radius=self.radius,
                include_sold=self.include_sold,
                listing_type=listing_type,
                page=page
            )

            # Scrape sites individually for better control and debugging
            logger.info("[Combined] Starting Rightmove scraping...")
            rightmove_results = await self.scrape_rightmove(
                location=location,
                min_price=min_price,
                max_price=max_price,
                min_beds=min_beds,
                max_beds=max_beds,
                listing_type=listing_type,
                page=page,
                keywords=keywords
            )

            # Print Rightmove results
            if rightmove_results and isinstance(rightmove_results, dict):
                logger.info("\n=== Rightmove Results ===")
                logger.info(f"Total listings found: {len(rightmove_results.get('listings', []))}")
                for listing in rightmove_results.get('listings', []):
                    logger.info(f"\nTitle: {listing.get('title')}")
                    logger.info(f"Price: {listing.get('price')}")
                    logger.info(f"URL: {listing.get('url')}")
                    logger.info("-" * 50)

            logger.info("[Combined] Starting Zoopla scraping...")
            zoopla_results = await self.scrape_zoopla(
                location=location,
                min_price=min_price,
                max_price=max_price,
                min_beds=min_beds,
                max_beds=max_beds,
                listing_type=listing_type,
                page=page,
                keywords=keywords
            )

            # Print Zoopla results
            if zoopla_results and isinstance(zoopla_results, dict):
                logger.info("\n=== Zoopla Results ===")
                logger.info(f"Total listings found: {len(zoopla_results.get('listings', []))}")
                for listing in zoopla_results.get('listings', []):
                    logger.info(f"\nTitle: {listing.get('title')}")
                    logger.info(f"Price: {listing.get('price')}")
                    logger.info(f"URL: {listing.get('url')}")
                    logger.info("-" * 50)

            # Initialize empty results if either scraper failed
            if not rightmove_results or not isinstance(rightmove_results, dict):
                rightmove_results = {"listings": [], "total_pages": 1}
            if not zoopla_results or not isinstance(zoopla_results, dict):
                zoopla_results = {"listings": [], "total_pages": 1}

            # Extract listings and metadata with better error handling
            rightmove_listings = []
            if rightmove_results and isinstance(rightmove_results, dict):
                rightmove_listings = rightmove_results.get("listings", [])
                logger.info(f"[Combined] Processing {len(rightmove_listings)} Rightmove listings")
                # Add source field if missing
                for listing in rightmove_listings:
                    if "source" not in listing:
                        listing["source"] = "Rightmove"

            zoopla_listings = []
            if zoopla_results and isinstance(zoopla_results, dict):
                zoopla_listings = zoopla_results.get("listings", [])
                logger.info(f"[Combined] Processing {len(zoopla_listings)} Zoopla listings")

            # Debug logging
            logger.info(f"[Combined] Rightmove listings found: {len(rightmove_listings)}")
            logger.info(f"[Combined] Zoopla listings found: {len(zoopla_listings)}")

            # Create unique identifier for each listing
            unique_listings = {}
            
            # Process Rightmove listings
            for listing in rightmove_listings:
                key = (
                    listing.get("price", "").lower(),
                    listing.get("address", "").lower()
                )
                if key not in unique_listings:
                    unique_listings[key] = listing

            # Process Zoopla listings
            for listing in zoopla_listings:
                key = (
                    listing.get("price", "").lower(),
                    listing.get("address", "").lower()
                )
                if key not in unique_listings:
                    unique_listings[key] = listing

            # Get final deduplicated list
            combined_listings = list(unique_listings.values())

            # Calculate stats
            rightmove_total = len(rightmove_listings)
            zoopla_total = len(zoopla_listings)
            
            site_stats = {
                "rightmove": {
                    "total_found": rightmove_total,
                    "processed": len(rightmove_listings)
                },
                "zoopla": {
                    "total_found": zoopla_total,
                    "processed": len(zoopla_listings)
                }
            }

            # Get total pages from both sources
            rightmove_total_pages = rightmove_results.get("total_pages", 1)
            zoopla_total_pages = (
                zoopla_results.get("total_pages", 1) 
                if isinstance(zoopla_results, dict) 
                else 1
            )

            logger.info(f"[Combined] Found {len(combined_listings)} unique listings")
            logger.info(f"[Combined] Rightmove: {rightmove_total} listings")
            logger.info(f"[Combined] Zoopla: {zoopla_total} listings")

            return {
                "listings": combined_listings,
                "site_stats": site_stats,
                "total_found": len(combined_listings),
                "total_pages": max(rightmove_total_pages, zoopla_total_pages),
                "current_page": page,
                "has_next_page": page < max(rightmove_total_pages, zoopla_total_pages)
            }

        except Exception as e:
            logger.error(f"[Combined ERROR] {str(e)}")
            return {
                "listings": [],
                "site_stats": {},
                "total_found": 0,
                "total_pages": 1,
                "current_page": page,
                "has_next_page": False
            }

async def main():
    bot = ScraperBot()
    await bot.scrape_all_combinations()

if __name__ == "__main__":
    asyncio.run(main())