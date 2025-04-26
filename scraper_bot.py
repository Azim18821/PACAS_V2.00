
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from utils.database import Database
from utils.logger import logger
from scrapers.rightmove_url import get_final_rightmove_results_url
from scrapers.rightmove_scrape import scrape_rightmove_from_url

# Load environment variables
load_dotenv()

class ScraperBot:
    def __init__(self):
        self.db = Database()
        self.radius = "0.0"  # Default radius for location search
        self.sort_by = "newest"  # Default sort order
        self.include_sold = True  # Include sold properties

    async def scrape_rightmove(self, location, min_price, max_price, min_beds, max_beds, listing_type, page=1, keywords=""):
        """Scrape Rightmove listings"""
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

            # Add small delay between requests
            await asyncio.sleep(2)

            # Direct scraping using rightmove_scrape
            logger.info("[Rightmove] Starting scraping...")
            results = scrape_rightmove_from_url(url, page=page)
            
            if results and isinstance(results, dict):
                listings = results.get('listings', [])
                logger.info(f"[Rightmove] Found {len(listings)} listings")
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

if __name__ == "__main__":
    bot = ScraperBot()
