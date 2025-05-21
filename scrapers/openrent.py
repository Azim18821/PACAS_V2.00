
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

def scrape_openrent(location, min_price="", max_price="", min_beds="", page=1):
    try:
        # Format search parameters
        params = {
            'term': location.strip(),
            'prices_min': min_price if min_price else None,
            'prices_max': max_price if max_price else None,
            'bedrooms_min': min_beds if min_beds else None,
            'bedrooms_max': max_beds if max_beds else None,
            'acceptStudents': 'true',
            'includeBills': 'true'
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
            
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

                # Extract price with more specific selectors
                price = "Price not specified"
                try:
                    # Try multiple price selectors
                    price_elem = (
                        card.select_one(".pli__price") or  # Primary price selector
                        card.select_one(".listing-price") or
                        card.select_one(".propertyCard-priceValue") or
                        card.select_one("[data-price]")
                    )
                    
                    if price_elem:
                        price_text = price_elem.text.strip()
                        # Remove any non-price text
                        price_text = ''.join(c for c in price_text if c.isdigit() or c in '£,.')
                        if price_text:
                            # Format price consistently
                            price_text = price_text.replace(',', '')
                            if not price_text.startswith('£'):
                                price_text = f'£{price_text}'
                            # Add pcm for rental listings
                            if 'rent' in card.get('href', '').lower():
                                price_text += ' pcm'
                            price = price_text
                    else:
                        # Try finding price in the listing text
                        listing_text = card.get_text()
                        import re
                        price_match = re.search(r'£(\d{2,4}(?:,\d{3})*(?:\.\d{2})?)', listing_text)
                        if price_match:
                            price = f"£{price_match.group(1)} pcm"
                except Exception as e:
                    logging.error(f"Error extracting price: {str(e)}")

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
