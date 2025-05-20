
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
        self.max_retries = 3
        self.retry_delay = 5

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
                
                # Add source to listings
                for listing in listings:
                    listing['source'] = 'Rightmove'
                
                return results

            logger.warning("[Rightmove] No results dictionary returned")
            return None

        except Exception as e:
            logger.error(f"[Rightmove ERROR] {str(e)}")
            return None

    async def scrape_zoopla(self, location, min_price, max_price, min_beds, max_beds, listing_type, page=1, keywords=""):
        """Scrape Zoopla listings"""
        try:
            # Check cache first
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
            
            if cached_results:
                logger.info("[Zoopla] Using cached results")
                return cached_results

            # Import Zoopla scraper dynamically to avoid circular imports
            from scrapers.zoopla import scrape_zoopla_first_page, scrape_zoopla_page

            await asyncio.sleep(2)  # Add delay between requests

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
                total_pages = page

            if results:
                # Add source to listings
                for listing in results:
                    listing['source'] = 'Zoopla'

                structured_results = {
                    "listings": results,
                    "total_found": len(results) * total_pages,
                    "total_pages": total_pages,
                    "current_page": page,
                    "has_next_page": page < total_pages,
                    "is_complete": page >= total_pages
                }

                # Cache results
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

            return None

        except Exception as e:
            logger.error(f"[Zoopla ERROR] {str(e)}")
            return None

    def normalize_address(self, address):
        """Normalize address for comparison by removing spaces, commas and converting to lowercase"""
        if not address:
            return ""
        return ''.join(c.lower() for c in address if c.isalnum())

    def is_duplicate_listing(self, listing, existing_listings):
        """Check if listing is duplicate based on normalized address or URL"""
        new_address = self.normalize_address(listing.get('address', ''))
        new_url = listing.get('url', '').lower()
        
        for existing in existing_listings:
            # Check for duplicate addresses
            if new_address and new_address == self.normalize_address(existing.get('address', '')):
                return True
            # Check for duplicate URLs
            if new_url and new_url == existing.get('url', '').lower():
                return True
        return False

    async def scrape_combined(self, location, min_price, max_price, min_beds, max_beds, listing_type, page=1, keywords=""):
        """Scrape both Rightmove and Zoopla and combine results with deduplication"""
        try:
            # Check combined cache first
            cached_results = self.db.get_cached_results(
                site="Combined",
                location=location,
                min_price=min_price,
                max_price=max_price,
                min_beds=min_beds,
                max_beds=max_beds,
                keywords=keywords,
                listing_type=listing_type,
                page_number=page
            )
            
            if cached_results:
                logger.info("[Combined] Using cached results")
                return cached_results

            # Scrape all sites concurrently
            rightmove_task = asyncio.create_task(
                self.scrape_rightmove(location, min_price, max_price, min_beds, max_beds, listing_type, page, keywords)
            )
            zoopla_task = asyncio.create_task(
                self.scrape_zoopla(location, min_price, max_price, min_beds, max_beds, listing_type, page, keywords)
            )
            
            # Only include OpenRent for rental listings
            tasks = [rightmove_task, zoopla_task]
            if listing_type == "rent":
                openrent_task = asyncio.create_task(
                    self.scrape_openrent(location, min_price, max_price, min_beds, max_beds, page, keywords)
                )
                tasks.append(openrent_task)
                
            results = await asyncio.gather(*tasks)
            rightmove_results = results[0]
            zoopla_results = results[1]
            openrent_results = results[2] if listing_type == "rent" else None

            # Combine results with deduplication
            combined_listings = []
            total_pages = 1
            
            # Add Rightmove listings first
            if rightmove_results:
                for listing in rightmove_results.get('listings', []):
                    if not self.is_duplicate_listing(listing, combined_listings):
                        combined_listings.append(listing)
                total_pages = max(total_pages, rightmove_results.get('total_pages', 1))
            
            # Add non-duplicate Zoopla listings
            if zoopla_results:
                for listing in zoopla_results.get('listings', []):
                    if not self.is_duplicate_listing(listing, combined_listings):
                        combined_listings.append(listing)
                total_pages = max(total_pages, zoopla_results.get('total_pages', 1))
            
            # Add non-duplicate OpenRent listings for rentals
            if listing_type == "rent" and openrent_results:
                for listing in openrent_results.get('listings', []):
                    if not self.is_duplicate_listing(listing, combined_listings):
                        combined_listings.append(listing)
                total_pages = max(total_pages, openrent_results.get('total_pages', 1))

    async def scrape_openrent(self, location, min_price, max_price, min_beds, max_beds, page=1, keywords=""):
        """Scrape OpenRent listings"""
        try:
            # Check cache first
            cached_results = self.db.get_cached_results(
                site="OpenRent",
                location=location,
                min_price=min_price,
                max_price=max_price,
                min_beds=min_beds,
                max_beds=max_beds,
                keywords=keywords,
                listing_type="rent",  # OpenRent is rentals only
                page_number=page
            )
            
            if cached_results:
                logger.info("[OpenRent] Using cached results")
                return cached_results

            # Add small delay between requests
            await asyncio.sleep(2)

            # Use the existing OpenRent scraper
            from scrapers.openrent import scrape_openrent
            listings = scrape_openrent(
                location=location,
                min_price=min_price,
                max_price=max_price,
                min_beds=min_beds,
                keywords=keywords
            )

            # Structure results to match other scrapers
            results = {
                'listings': listings,
                'total_found': len(listings),
                'total_pages': 1,  # OpenRent currently doesn't support pagination
                'current_page': page,
                'has_next_page': False,
                'is_complete': True
            }

            # Cache results
            if listings:
                self.db.cache_results(
                    site="OpenRent",
                    location=location,
                    min_price=min_price,
                    max_price=max_price,
                    min_beds=min_beds,
                    max_beds=max_beds,
                    keywords=keywords,
                    listing_type="rent",
                    page_number=page,
                    results=results
                )

            return results

        except Exception as e:
            logger.error(f"[OpenRent ERROR] {str(e)}")
            return None

            # Create combined results structure
            combined_results = {
                "listings": combined_listings,
                "total_found": len(combined_listings),
                "total_pages": total_pages,
                "current_page": page,
                "has_next_page": page < total_pages,
                "is_complete": page >= total_pages
            }

            # Cache combined results
            self.db.cache_results(
                site="Combined",
                location=location,
                min_price=min_price,
                max_price=max_price,
                min_beds=min_beds,
                max_beds=max_beds,
                keywords=keywords,
                listing_type=listing_type,
                page_number=page,
                results=combined_results
            )

            return combined_results

        except Exception as e:
            logger.error(f"[Combined ERROR] {str(e)}")
            return None

if __name__ == "__main__":
    bot = ScraperBot()
    asyncio.run(bot.scrape_combined("london", "0", "1000000", "1", "3", "sale"))
