"""Find the exact relationship between cards and images"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

def get_proxy_url(url):
    api_key = os.getenv('SCRAPER_API_KEY')
    return f"http://api.scraperapi.com?api_key={api_key}&url={url}"

async def map_cards_to_images():
    test_url = "https://www.zoopla.co.uk/for-sale/property/manchester/?price_max=10000000&beds_max=10&q=manchester&search_source=for-sale&pn=1"
    
    async with aiohttp.ClientSession() as session:
        proxy_url = get_proxy_url(test_url)
        async with session.get(proxy_url) as response:
            html = await response.text()
    
    soup = BeautifulSoup(html, "html.parser")
    
    cards = soup.find_all("a", {"data-testid": "listing-card-content"})
    pictures = soup.find_all("picture")
    
    print(f"Cards: {len(cards)}, Pictures: {len(pictures)}\n")
    print("="*80)
    
    # Check if they're in the same parent container
    for idx in range(min(3, len(cards))):
        card = cards[idx]
        picture = pictures[idx] if idx < len(pictures) else None
        
        print(f"\nCARD {idx+1}:")
        print(f"  href: {card.get('href')}")
        
        # Get the card's parent container
        container = card.parent.parent if card.parent else None
        
        if container:
            print(f"  Container: {container.name}, class: {container.get('class')}")
            
            # Find pictures in the same container
            pics_in_container = container.find_all("picture")
            print(f"  Pictures in same container: {len(pics_in_container)}")
            
            if pics_in_container:
                pic = pics_in_container[0]
                sources = pic.find_all("source")
                if sources:
                    srcset = sources[0].get("srcset", "")
                    # Extract first URL from srcset
                    first_url = srcset.split(",")[0].split()[0] if srcset else ""
                    print(f"  Image URL: {first_url[:80]}...")
        
        print("-"*80)
    
    # Try to find the exact parent structure
    print("\n" + "="*80)
    print("DETAILED STRUCTURE FOR FIRST LISTING")
    print("="*80)
    
    if cards and pictures:
        card = cards[0]
        pic = pictures[0]
        
        # Find common ancestor
        card_parents = []
        p = card
        while p:
            card_parents.append(p)
            p = p.parent
        
        pic_parents = []
        p = pic
        while p:
            pic_parents.append(p)
            p = p.parent
        
        # Find first common ancestor
        common = None
        for cp in card_parents:
            if cp in pic_parents:
                common = cp
                break
        
        if common:
            print(f"\nCommon ancestor: {common.name}, class: {common.get('class')}")
            
            # Show structure
            print("\nCard path from common ancestor:")
            idx = card_parents.index(common)
            for i in range(idx, -1, -1):
                indent = "  " * (idx - i)
                elem = card_parents[i]
                print(f"{indent}{elem.name} {elem.get('class', '')}")
            
            print("\nPicture path from common ancestor:")
            idx = pic_parents.index(common)
            for i in range(idx, -1, -1):
                indent = "  " * (idx - i)
                elem = pic_parents[i]
                print(f"{indent}{elem.name} {elem.get('class', '')}")

if __name__ == "__main__":
    asyncio.run(map_cards_to_images())
