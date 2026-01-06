import requests
import os
from dotenv import load_dotenv
from utils.logger import logger
from bs4 import BeautifulSoup
import time
import random
import asyncio
import aiohttp
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

# Zoopla sort options mapping
ZOOPLA_SORT_OPTIONS = {
    "newest": "newest_listings",
    "oldest": "oldest_listings",
    "price_asc": "price_ascending",
    "price_desc": "price_descending",
    "beds_asc": "beds_ascending",
    "beds_desc": "beds_descending",
    "most_viewed": "most_popular",
    "reduced": "most_reduced",
    "most_reduced": "most_reduced",
    "distance": "nearest"
}

# Load environment variables from .env
logger.info("[Zoopla] Loading environment variables...")
logger.info("[Zoopla] Current working directory: %s", os.getcwd())
logger.info("[Zoopla] Looking for .env file...")
if os.path.exists('.env'):
    logger.info("[Zoopla] .env file found")
    with open('.env', 'r') as f:
        logger.info("[Zoopla] .env contents: %s", f.read())
else:
    logger.error("[Zoopla] .env file not found!")

load_dotenv(override=True)  # Force reload of environment variables
logger.info("[Zoopla] Environment variables loaded")
logger.info("[Zoopla] All environment variables: %s", dict(os.environ))

# Cache for proxy URLs to avoid regenerating them
@lru_cache(maxsize=100)
def get_proxy_url(url):
    """Get ScraperAPI URL with API key"""
    logger.info("[Zoopla] Getting ScraperAPI key...")
    api_key = os.getenv('SCRAPER_API_KEY')
    logger.info("[Zoopla] ScraperAPI key found: %s", "Yes" if api_key else "No")
    if api_key:
        logger.info("[Zoopla] ScraperAPI key length: %d", len(api_key))
    
    if not api_key:
        logger.error("[Zoopla] No ScraperAPI key found in environment variables")
        logger.error("[Zoopla] Available environment variables: %s", list(os.environ.keys()))
        # Try to load the .env file directly
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('SCRAPER_API_KEY='):
                        api_key = line.strip().split('=')[1]
                        logger.info("[Zoopla] Found ScraperAPI key in .env file")
                        break
        except Exception as e:
            logger.error("[Zoopla] Error reading .env file: %s", str(e))
        
        if not api_key:
            raise ValueError("SCRAPER_API_KEY not found in environment variables or .env file")
    
    proxy_url = f"http://api.scraperapi.com?api_key={api_key}&url={url}"
    logger.info("[Zoopla] Using ScraperAPI URL (key masked): %s", proxy_url.replace(api_key, "XXXXX"))
    return proxy_url

async def fetch_page(session, url):
    """Fetch a single page asynchronously"""
    try:
        proxy_url = get_proxy_url(url)
        async with session.get(proxy_url) as response:
            if response.status == 200:
                return await response.text()
            logger.error(f"[Zoopla] Request failed with status code: {response.status}")
            return None
    except Exception as e:
        logger.error(f"[Zoopla] Error fetching page: {str(e)}")
        return None

def parse_card(card):
    """Parse a single card into a listing"""
    try:
        # Try multiple selectors for price
        price = (
            card.select_one('[data-testid="listing-price"]') or
            card.select_one('.listing-details .price') or
            card.select_one('.text-price')
        )
        price = price.text.strip() if price else ""

        # Try multiple selectors for specs
        specs_raw = (
            card.find("p", class_="_1wickv3") or
            card.find("ul", class_="listing-details") or
            card.find("span", class_="num-beds")
        )
        specs = " ".join(span.text.strip() for span in specs_raw.find_all(["span", "li"])) if specs_raw else ""

        # Try multiple selectors for address
        address = (
            card.find("address") or
            card.find("a", class_="listing-results-address")
        )
        address = address.text.strip() if address else ""

        # Get description
        desc = card.find_all("p")[-1].text.strip() if card.find_all("p") else ""

        # Get link
        url = "https://www.zoopla.co.uk" + (
            card.get("href", "") if card.name == "a" 
            else card.find("a").get("href", "") if card.find("a") 
            else ""
        )

        # Search for image - Zoopla has images in a sibling structure
        image = ""
        # The card and picture are siblings within a common parent container
        # Walk up to find the common ancestor (usually 5-6 levels up)
        parent = card
        for _ in range(6):
            parent = parent.parent if parent else None
            if parent:
                # Look for picture tag with srcset in this container
                picture_tag = parent.find("picture")
                if picture_tag:
                    source_tag = picture_tag.find("source")
                    if source_tag and source_tag.has_attr("srcset"):
                        srcset = source_tag["srcset"]
                        # Extract first URL from srcset (format: "url width, url width, ...")
                        image = srcset.split(",")[0].split()[0]
                        break
        
        if not image:
            # Fallback to other image selectors if parent walk fails
            img_tag = (
                card.find("img", {"data-src": True}) or
                card.find("img", {"src": True}) or
                card.find("source", {"srcset": True})
            )
            if img_tag:
                image = img_tag.get("data-src") or img_tag.get("src") or img_tag.get("srcset", "").split(",")[0].split()[0]

        return {
            "title": desc or address,
            "price": price,
            "address": address,
            "desc": desc,
            "specs": specs,
            "image": image,
            "url": url,
            "source": "Zoopla"
        }
    except Exception as e:
        logger.error(f"[Zoopla] Failed to parse card: {str(e)}")
        return None

async def scrape_zoopla_first_page(location, min_price="", max_price="", min_beds="", max_beds="", keywords="", listing_type="sale", page_number=1, sort_by="newest"):
    """Scrape only the first page of Zoopla listings and return total pages"""
    logger.info("[Zoopla] Starting scrape_zoopla_first_page function with sort_by: %s", sort_by)
    
    location_url = location.strip().replace(" ", "-").lower()

    base_url = (
        f"https://www.zoopla.co.uk/to-rent/property/{location_url}/"
        if listing_type == "rent"
        else f"https://www.zoopla.co.uk/for-sale/property/{location_url}/"
    )

    filters = []
    # Convert price values to strings and ensure they're not empty
    if min_price and str(min_price).strip() and float(min_price) > 0:
        filters.append(f"price_min={str(min_price)}")
    if max_price and str(max_price).strip() and float(max_price) < float('inf'):
        filters.append(f"price_max={str(max_price)}")
    
    if min_beds and str(min_beds).strip():
        filters.append(f"beds_min={str(min_beds)}")
    if max_beds and str(max_beds).strip():
        filters.append(f"beds_max={str(max_beds)}")
    
    filters.extend([
        "q=" + location.replace(" ", "%20"),
        "search_source=for-sale" if listing_type == "sale" else "search_source=to-rent",
        f"pn={str(page_number)}",  # Add page number
        f"results_sort={ZOOPLA_SORT_OPTIONS.get(sort_by, 'newest_listings')}"  # Add sort option (Zoopla uses 'results_sort' parameter)
    ])

    query = "?" + "&".join(filters) if filters else ""
    full_url = base_url + query
    
    logger.info(f"[Zoopla] Full URL: {full_url}")
    
    async with aiohttp.ClientSession() as session:
        html = await fetch_page(session, full_url)
        if not html:
            logger.error("[Zoopla] Failed to fetch page")
            return [], 0

        soup = BeautifulSoup(html, "html.parser")
        cards = (
            soup.find_all("a", {"data-testid": "listing-card-content"}) or
            soup.find_all("div", class_="listing-results-wrapper") or
            soup.find_all("div", {"data-listing-id": True})
        )
        
        logger.info(f"[Zoopla] Found {len(cards)} cards on page")

        first_page_listings = []
        for card in cards:
            listing = parse_card(card)
            if listing:
                text_to_search = " ".join([listing["price"], listing["specs"], listing["address"], listing["desc"]]).lower()
                if not keywords or keywords.lower() in text_to_search:
                    first_page_listings.append(listing)

        logger.info(f"[Zoopla] Parsed {len(first_page_listings)} listings")

        # Get total pages
        total_pages = 1
        pagination = soup.find("div", {"data-testid": "pagination"})
        if pagination:
            page_links = pagination.find_all("a")
            if page_links:
                for link in reversed(page_links):
                    try:
                        total_pages = int(link.text.strip())
                        break
                    except ValueError:
                        continue

        logger.info(f"[Zoopla] Total pages found: {total_pages}")
        return first_page_listings, total_pages

async def scrape_zoopla_page(location, min_price="", max_price="", min_beds="", max_beds="", keywords="", listing_type="sale", page_num=1, sort_by="newest"):
    """Scrape a specific page of Zoopla listings"""
    logger.info(f"[Zoopla] Starting scrape_zoopla_page function for page {page_num} with sort_by: {sort_by}")
    
    location_url = location.strip().replace(" ", "-").lower()

    base_url = (
        f"https://www.zoopla.co.uk/to-rent/property/{location_url}/"
        if listing_type == "rent"
        else f"https://www.zoopla.co.uk/for-sale/property/{location_url}/"
    )

    filters = []
    # Convert price values to strings and ensure they're not empty
    if min_price and str(min_price).strip() and float(min_price) > 0:
        filters.append(f"price_min={str(min_price)}")
    if max_price and str(max_price).strip() and float(max_price) < float('inf'):
        filters.append(f"price_max={str(max_price)}")
    
    if min_beds and str(min_beds).strip():
        filters.append(f"beds_min={str(min_beds)}")
    if max_beds and str(max_beds).strip():
        filters.append(f"beds_max={str(max_beds)}")
    
    filters.extend([
        "q=" + location.replace(" ", "%20"),
        "search_source=for-sale" if listing_type == "sale" else "search_source=to-rent",
        f"pn={page_num}",
        f"results_sort={ZOOPLA_SORT_OPTIONS.get(sort_by, 'newest_listings')}"  # Add sort option
    ])

    query = "?" + "&".join(filters) if filters else ""
    page_url = base_url + query
    
    logger.info(f"[Zoopla] Page URL: {page_url}")
    
    async with aiohttp.ClientSession() as session:
        html = await fetch_page(session, page_url)
        if not html:
            logger.error("[Zoopla] Failed to fetch page")
            return []

        soup = BeautifulSoup(html, "html.parser")
        cards = (
            soup.find_all("a", {"data-testid": "listing-card-content"}) or
            soup.find_all("div", class_="listing-results-wrapper") or
            soup.find_all("div", {"data-listing-id": True})
        )
        
        logger.info(f"[Zoopla] Found {len(cards)} cards on page {page_num}")

        page_listings = []
        for card in cards:
            listing = parse_card(card)
            if listing:
                text_to_search = " ".join([listing["price"], listing["specs"], listing["address"], listing["desc"]]).lower()
                if not keywords or keywords.lower() in text_to_search:
                    page_listings.append(listing)

        logger.info(f"[Zoopla] Parsed {len(page_listings)} listings from page {page_num}")
        return page_listings

async def scrape_zoopla(location, min_price="", max_price="", min_beds="", max_beds="", keywords="", listing_type="sale"):
    """Scrape all Zoopla listings (for backward compatibility)"""
    first_page_results, total_pages = await scrape_zoopla_first_page(
        location, min_price, max_price, min_beds, max_beds, keywords, listing_type
    )
    return first_page_results
