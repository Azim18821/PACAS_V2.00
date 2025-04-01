import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")

def get_proxy_url(url):
    return f"https://api.scraperapi.com/?api_key={SCRAPERAPI_KEY}&url={url}"

def scrape_openrent(location, min_price="", max_price="", min_beds="", keywords=""):
    # Format the location properly for the URL
    search_location = location.strip().replace(" ", "+")
    base_url = f"https://www.openrent.co.uk/properties-to-rent/{search_location}"
    proxy_url = get_proxy_url(base_url)  # Use the correctly formatted URL

    print(f"[OpenRent] Scraping through ScraperAPI with URL: {proxy_url}")

    try:
        res = requests.get(proxy_url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            print("[OpenRent] Successfully fetched the data")
        else:
            print(f"[OpenRent] Failed to fetch data: Status code {res.status_code}")
        
        soup = BeautifulSoup(res.text, "html.parser")
    except Exception as e:
        print("[OpenRent ERROR] Request failed:", e)
        return []

    # Find the property cards on the page using the correct CSS selector
    cards = soup.select("a.pli.clearfix")  # This is the selector for property cards
    print(f"[OpenRent] Found {len(cards)} property cards")

    # If no cards are found, check for an issue with the selector or page content
    if len(cards) == 0:
        print("[OpenRent ERROR] No property cards found. Verify if the CSS selector is correct.")

    listings = []
    for idx, card in enumerate(cards):
        try:
            # Extract the image URL from the card
            img_tag = card.select_one("img.propertyPic")
            image = ""
            if img_tag:
                image = img_tag.get("src") or img_tag.get("data-src") or ""
            print(f"[OpenRent DEBUG] Card {idx + 1} image: {image}")

            # Extract the title, address, price, and description
            title = card.select_one(".listing-title")
            address = card.select_one(".listing-title")
            price = card.select_one(".or-price")
            desc = card.select_one(".or-description")
            link_tag = card.select_one("a")

            listings.append({
                "title": title.text.strip() if title else "",
                "price": price.text.strip() if price else "N/A",  # Default to "N/A" if no price
                "address": address.text.strip() if address else "",
                "desc": desc.text.strip() if desc else "",
                "specs": "",  # optional: parse bed count here if needed
                "image": image,
                "link": "https://www.openrent.co.uk" + link_tag["href"] if link_tag else "",
                "source": "OpenRent"
            })

        except Exception as e:
            print(f"[OpenRent ERROR] Card {idx + 1} parsing failed:", e)

    return listings
