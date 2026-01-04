"""Test script to check Zoopla image extraction"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

def get_proxy_url(url):
    """Get ScraperAPI URL with API key"""
    api_key = os.getenv('SCRAPER_API_KEY')
    return f"http://api.scraperapi.com?api_key={api_key}&url={url}"

async def test_zoopla_images():
    """Test Zoopla image extraction"""
    test_url = "https://www.zoopla.co.uk/for-sale/property/manchester/?price_max=10000000&beds_max=10&q=manchester&search_source=for-sale&pn=1"
    
    print(f"Testing URL: {test_url}")
    print("-" * 80)
    
    async with aiohttp.ClientSession() as session:
        proxy_url = get_proxy_url(test_url)
        async with session.get(proxy_url) as response:
            html = await response.text()
            
    soup = BeautifulSoup(html, "html.parser")
    
    # Find cards
    cards = soup.find_all("a", {"data-testid": "listing-card-content"})
    print(f"Found {len(cards)} property cards\n")
    
    if len(cards) > 0:
        # Check first 2 cards
        for idx, card in enumerate(cards[:2]):
            print(f"\n{'='*80}")
            print(f"CARD {idx + 1}")
            print(f"{'='*80}")
            
            # Check for images in different ways
            print("\n1. Direct img tags in card:")
            imgs = card.find_all("img")
            for i, img in enumerate(imgs):
                print(f"   Img {i+1}:")
                print(f"      src: {img.get('src', 'N/A')}")
                print(f"      data-src: {img.get('data-src', 'N/A')}")
                print(f"      srcset: {img.get('srcset', 'N/A')}")
            
            print("\n2. Source tags in card:")
            sources = card.find_all("source")
            for i, source in enumerate(sources):
                print(f"   Source {i+1}:")
                print(f"      srcset: {source.get('srcset', 'N/A')}")
                print(f"      type: {source.get('type', 'N/A')}")
            
            print("\n3. Picture tags in card:")
            pictures = card.find_all("picture")
            for i, pic in enumerate(pictures):
                print(f"   Picture {i+1}: {len(pic.find_all('source'))} source tags, {len(pic.find_all('img'))} img tags")
            
            # Try current extraction logic
            print("\n4. Current extraction logic result:")
            image = ""
            parent = card
            for level in range(6):  # Increased to 6 levels
                parent = parent.parent if parent else None
                if parent:
                    picture_tag = parent.find("picture")
                    if picture_tag:
                        source_tag = picture_tag.find("source")
                        if source_tag and source_tag.has_attr("srcset"):
                            srcset = source_tag["srcset"]
                            image = srcset.split(",")[0].split()[0]
                            print(f"   Found in parent level {level+1}: {image}")
                            break
            
            if not image:
                print("   No image found via parent walk, trying fallback...")
                img_tag = (
                    card.find("img", {"data-src": True}) or
                    card.find("img", {"src": True}) or
                    card.find("source", {"srcset": True})
                )
                if img_tag:
                    image = img_tag.get("data-src") or img_tag.get("src") or img_tag.get("srcset", "").split(",")[0].split()[0]
                    print(f"   Fallback found: {image}")
                else:
                    print("   No image found at all!")
            
            # Show a snippet of the card HTML
            print("\n5. Card HTML snippet (first 500 chars):")
            print(f"   {str(card)[:500]}...")

if __name__ == "__main__":
    asyncio.run(test_zoopla_images())
