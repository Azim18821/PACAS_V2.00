"""
OpenRent Scraper - TEMPORARILY DISABLED

OpenRent uses AWS WAF (Web Application Firewall) with JavaScript challenge
which blocks simple HTTP requests. This requires browser automation (Selenium/Playwright)
or Apify Actor integration to work properly.

TODO: Implement proper solution using:
- Option 1: Apify Actor for OpenRent
- Option 2: Selenium/Playwright browser automation
"""

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging
import time
from urllib.parse import urlencode

load_dotenv()
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")

def get_proxy_url(url):
    return f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"

def scrape_openrent(location, min_price="", max_price="", min_beds="", keywords="", page=1):
    try:
        # Format search parameters
        params = {
            'term': location.strip(),
            'sortType': 'newestFirst'
        }
        
        if min_price:
            params['prices_min'] = min_price
        if max_price:
            params['prices_max'] = max_price
        if min_beds:
            params['bedrooms_min'] = min_beds
            
        # Build URL with parameters
        base_url = "https://www.openrent.co.uk/properties-to-rent"
        search_url = f"{base_url}?{urlencode(params)}"
        if page > 1:
            search_url += f"&page={page}"

        # Use proxy
        proxy_url = get_proxy_url(search_url)
        logging.info(f"[OpenRent] Scraping page {page}: {search_url}")

        # Make request with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    proxy_url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=30
                )
                response.raise_for_status()
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"[OpenRent] Failed after {max_retries} attempts: {str(e)}")
                    return {
                        "listings": [],
                        "total_found": 0,
                        "total_pages": 0,
                        "current_page": page,
                        "has_next_page": False,
                        "is_complete": True
                    }
                time.sleep(2 ** attempt)  # Exponential backoff

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract total results and pages
        total_results = 0
        total_results_elem = soup.select_one('.searchTitle')
        if total_results_elem:
            try:
                total_text = total_results_elem.text
                total_results = int(''.join(filter(str.isdigit, total_text)))
            except:
                logging.warning("[OpenRent] Could not parse total results")

        # Calculate total pages (24 results per page)
        total_pages = (total_results + 23) // 24 if total_results > 0 else 1
        
        # Find all property listings
        listings = []
        property_cards = soup.select("a.pli")
        
        for card in property_cards:
            try:
                # Extract image
                img_elem = card.select_one("img.propertyPic")
                image_url = img_elem.get('data-src') or img_elem.get('src') if img_elem else ""

                # Extract price
                price_elem = card.select_one(".price")
                price = price_elem.text.strip() if price_elem else "Price not specified"

                # Extract title and address
                title_elem = card.select_one(".banda")
                title = title_elem.text.strip() if title_elem else ""

                # Extract description
                desc_elem = card.select_one(".description")
                description = desc_elem.text.strip() if desc_elem else ""

                # Extract property link
                property_url = "https://www.openrent.co.uk" + card['href'] if card.has_attr('href') else ""

                # Extract property ID from URL
                property_id = property_url.split('/')[-1] if property_url else None

                listing = {
                    "title": title,
                    "price": price,
                    "address": title,  # OpenRent combines address in title
                    "description": description,
                    "image": image_url,
                    "url": property_url,
                    "property_id": property_id,
                    "source": "OpenRent"
                }
                
                listings.append(listing)

            except Exception as e:
                logging.error(f"[OpenRent] Error parsing listing: {str(e)}")
                continue

        results = {
            "listings": listings,
            "total_found": total_results,
            "total_pages": total_pages,
            "current_page": page,
            "has_next_page": page < total_pages,
            "is_complete": page >= total_pages
        }

        return results

    except Exception as e:
        logging.error(f"[OpenRent] Scraping error: {str(e)}")
        return {
            "listings": [],
            "total_found": 0,
            "total_pages": 0,
            "current_page": page,
            "has_next_page": False,
            "is_complete": True
        }
