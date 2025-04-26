import os
import asyncio
import random
from datetime import datetime
from dotenv import load_dotenv
from scrapers.rightmove_url import get_final_rightmove_results_url
from scrapers.rightmove_scrape import scrape_rightmove_from_url
from utils.database import Database
from utils.logger import logger

# Load environment variables
load_dotenv()

class ScraperBot:
    def __init__(self):
        self.db = Database()
        self.radius = "0.0"  # Default radius for location search
        self.include_sold = True  # Include sold properties
        self.sort_by = "newest"  # Default sort order

    async def scrape_rightmove(self, location, min_price, max_price, min_beds, max_beds, listing_type, page=1, keywords=""):
        """Scrape Rightmove with direct approach"""
        try:
            # Generate Rightmove URL
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

            # Direct scraping using rightmove_scrape
            logger.info("[Rightmove] Starting scraping...")
            results = scrape_rightmove_from_url(url, page=page)

            if results and isinstance(results, dict):
                listings = results.get('listings', [])
                logger.info(f"\n=== Rightmove Results ===")
                logger.info(f"Total listings found: {len(listings)}")

                for listing in listings:
                    logger.info(f"\nTitle: {listing.get('title')}")
                    logger.info(f"Price: {listing.get('price')}")
                    logger.info(f"URL: {listing.get('url')}")
                    logger.info("-" * 50)

                return results

            logger.warning("[Rightmove] No results dictionary returned")
            return {
                "listings": [],
                "total_found": 0,
                "total_pages": 1,
                "current_page": page,
                "has_next_page": False
            }

        except Exception as e:
            logger.error(f"[Rightmove ERROR] {str(e)}")
            return {
                "listings": [],
                "total_found": 0,
                "total_pages": 1,
                "current_page": page,
                "has_next_page": False
            }

    async def scrape_all_pages(self, location, min_price, max_price, min_beds, max_beds, listing_type, keywords=""):
        """Scrape all pages for Rightmove with improved error handling"""
        logger.info(f"\n[Scraper Bot] Starting scrape for {location} - {listing_type}")
        logger.info(f"Price range: £{min_price} - £{max_price}")
        logger.info(f"Bedrooms: {min_beds}-{max_beds}")
        if keywords:
            logger.info(f"Keywords: {keywords}")

        page = 1
        all_results = []

        while True:
            results = await self.scrape_rightmove(
                location=location,
                min_price=min_price,
                max_price=max_price,
                min_beds=min_beds,
                max_beds=max_beds,
                listing_type=listing_type,
                page=page,
                keywords=keywords
            )

            if not results or not results.get('listings'):
                break

            all_results.extend(results['listings'])

            if not results.get('has_next_page'):
                break

            page += 1
            await asyncio.sleep(random.uniform(2, 4))

        return {
            "listings": all_results,
            "total_found": len(all_results),
            "total_pages": page,
            "current_page": page,
            "has_next_page": False
        }

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


async def main():
    bot = ScraperBot()
    await bot.scrape_all_combinations()

if __name__ == "__main__":
    asyncio.run(main())