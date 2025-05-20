import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_proxy_url(url):
    """Get the proxy URL for ScraperAPI"""
    api_key = os.getenv("SCRAPER_API_KEY")
    if not api_key:
        raise ValueError("SCRAPER_API_KEY not found in environment variables")
    return f"http://api.scraperapi.com?api_key={api_key}&url={url}"

def scrape_rightmove_from_url(url, page=1, get_total_only=False):
    try:
        # Remove URL modification since we handle it in URL generation
        proxy_url = get_proxy_url(url)
        print(f"[Rightmove] Scraping page {page}:", proxy_url)

        res = requests.get(proxy_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")

        # Debug: Print all available classes in the HTML
        print("\n[Rightmove DEBUG] Available classes in HTML:")
        for element in soup.find_all(class_=True):
            print(f"Class: {element['class']}")

        # Debug: Print the full HTML if no cards are found
        cards = soup.select(".PropertyCard_propertyCardContainer__VSRSA")
        if not cards:
            print("\n[Rightmove DEBUG] No property cards found. Full HTML:")
            print(soup.prettify())

        # Check for "This isn't the place you're looking for" message
        no_results_message = soup.select_one(".no-results-message")
        if no_results_message and "This isn't the place you're looking for" in no_results_message.text:
            print("[Rightmove] No results found for this search combination")
            return {
                "listings": [],
                "total_found": 0,
                "total_pages": 0,
                "current_page": page,
                "has_next_page": False,
                "is_complete": True,
                "no_results": True
            }

        # Check if this is a rental listing
        is_rental = "property-to-rent" in url
        print(f"[Rightmove] Is rental listing: {is_rental}")
        
        # Get total number of results first
        total_results = 0
        results_count = soup.select_one(".searchHeader-resultCount")
        if results_count:
            try:
                total_results = int(results_count.text.strip().replace(",", "").split()[0])
                print(f"[Rightmove] Total results found: {total_results}")
            except:
                print("[Rightmove] Could not parse total results count")
        else:
            print("[Rightmove] Could not find results count element")

        # If we only need the total, return early
        if get_total_only:
            total_pages = (total_results + 23) // 24 if total_results > 0 else 247
            return total_pages

        # Use unified selector for both rental and sale listings
        cards = soup.select("[data-test='propertyCard']")
        if not cards:
            # Fallback selectors
            cards = soup.select(".propertyCard") or soup.select(".l-searchResult") or soup.select(".PropertyCard_propertyCardContainer__VSRSA")
        
        print(f"[Rightmove] Found {len(cards)} property cards on page {page}")
        
        # Debug: Print first card HTML if found
        if cards:
            print("\n[Rightmove DEBUG] First card HTML:")
            print(cards[0].prettify())

        listings = []
        for idx, card in enumerate(cards):
            try:
                # Unified selectors for both rental and sale
                price = (
                    card.select_one("[data-test='property-price']") or
                    card.select_one(".PropertyPrice_price__VL65t") or
                    card.select_one(".propertyCard-priceValue") or
                    card.select_one(".price-text")
                )
                
                title = (
                    card.select_one("[data-test='property-title']") or
                    card.select_one(".PropertyAddress_address__LYRPq") or
                    card.select_one(".propertyCard-title") or
                    card.select_one(".property-title")
                )
                
                address = (
                    card.select_one("[data-test='property-address']") or
                    card.select_one(".propertyCard-address") or
                    card.select_one(".property-address")
                )
                
                desc = (
                    card.select_one("[data-test='property-description']") or
                    card.select_one(".PropertyCardSummary_summary__oIv57") or
                    card.select_one(".propertyCard-description") or
                    card.select_one(".property-description")
                )
                
                link_tag = (
                    card.select_one("[data-test='property-link']") or
                    card.select_one("a.propertyCard-link") or
                    card.select_one("a[href*='/properties/']")
                )
                
                # Get image
                image = ""
                img = (
                    card.select_one("[data-test='property-image'] img") or
                    card.select_one(".PropertyCardImage_slide__B8bBX img") or
                    card.select_one('img[itemprop="image"]') or
                    card.select_one(".property-image img")
                )
                if img and img.has_attr("src"):
                    image = img["src"]

                # Debug: Print extracted elements
                print(f"\n[Rightmove DEBUG] Card {idx + 1} elements:")
                print(f"Price element: {price}")
                print(f"Title element: {title}")
                print(f"Link element: {link_tag}")

                # Extract property ID from URL
                property_id = None
                property_url = None
                if link_tag and link_tag.has_attr("href"):
                    href = link_tag["href"]
                    # Handle both relative and absolute URLs
                    if href.startswith("http"):
                        property_url = href
                    else:
                        property_url = "https://www.rightmove.co.uk" + href
                    
                    # Extract property ID from URL (e.g., /properties/123456789.html)
                    try:
                        property_id = href.split("/")[-1].split(".")[0]
                    except:
                        print(f"[Rightmove DEBUG] Card {idx + 1}: Could not extract property ID from URL")
                        print(f"[Rightmove DEBUG] URL: {property_url}")

                listing = {
                    "title": title.text.strip() if title else "",
                    "price": price.text.strip() if price else "",
                    "address": title.text.strip() if title else "" if is_rental else address.text.strip() if address else "",
                    "desc": desc.text.strip() if desc else "",
                    "specs": "",  # Optional: parse bed count here
                    "image": image,
                    "url": property_url,
                    "property_id": property_id,
                    "source": "Rightmove"
                }
                
                listings.append(listing)
                
                # Print each listing as it's scraped
                print(f"\n[Rightmove] Scraped listing {idx + 1}:")
                print(f"Title: {listing['title']}")
                print(f"Price: {listing['price']}")
                print(f"Property ID: {listing['property_id']}")
                print(f"URL: {listing['url']}")
                
            except Exception as e:
                print(f"[Rightmove Listing Error] Card {idx + 1}:", e)

        # Calculate total pages (24 items per page)
        if total_results > 0:
            total_pages = (total_results + 23) // 24
        else:
            # If we can't find total results, estimate based on current page and results
            if len(listings) > 0:
                # If we have results on this page, assume there are more pages
                total_pages = max(page + 1, 247)  # At least current page + 1, or default to 247
            else:
                # If no results on this page, we're probably at the end
                total_pages = page

        print(f"[Rightmove] Total pages: {total_pages}")
        print(f"[Rightmove] Current page: {page}")
        print(f"[Rightmove] Has next page: {page < total_pages}")

        return {
            "listings": listings,
            "total_found": total_results,
            "total_pages": total_pages,
            "current_page": page,
            "has_next_page": page < total_pages,
            "is_complete": page >= total_pages
        }
        
    except Exception as e:
        print("[Rightmove ERROR]", e)
        return {
            "listings": [],
            "total_found": 0,
            "total_pages": 247,  # Default to 247 even on error
            "current_page": page,
            "has_next_page": page < 247,  # Default to 247 even on error
            "is_complete": page >= 247  # Default to 247 even on error
        }
