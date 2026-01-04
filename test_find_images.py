"""Test script to find where Zoopla images actually are"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

def get_proxy_url(url):
    api_key = os.getenv('SCRAPER_API_KEY')
    return f"http://api.scraperapi.com?api_key={api_key}&url={url}"

async def find_zoopla_images():
    test_url = "https://www.zoopla.co.uk/for-sale/property/manchester/?price_max=10000000&beds_max=10&q=manchester&search_source=for-sale&pn=1"
    
    print(f"Fetching page...")
    async with aiohttp.ClientSession() as session:
        proxy_url = get_proxy_url(test_url)
        async with session.get(proxy_url) as response:
            html = await response.text()
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Find all images on the page
    print("\n" + "="*80)
    print("ALL IMG TAGS ON PAGE")
    print("="*80)
    all_imgs = soup.find_all("img")
    print(f"Total img tags found: {len(all_imgs)}\n")
    
    for idx, img in enumerate(all_imgs[:10]):  # First 10 images
        print(f"{idx+1}. Img tag:")
        print(f"   src: {img.get('src', 'N/A')[:100]}")
        print(f"   data-src: {img.get('data-src', 'N/A')[:100]}")
        print(f"   alt: {img.get('alt', 'N/A')[:50]}")
        print(f"   class: {img.get('class', 'N/A')}")
        print()
    
    # Find all picture tags
    print("\n" + "="*80)
    print("ALL PICTURE TAGS")
    print("="*80)
    pictures = soup.find_all("picture")
    print(f"Total picture tags: {len(pictures)}\n")
    
    for idx, pic in enumerate(pictures[:5]):
        print(f"{idx+1}. Picture tag:")
        sources = pic.find_all("source")
        imgs = pic.find_all("img")
        print(f"   Has {len(sources)} source tags, {len(imgs)} img tags")
        if sources:
            print(f"   First source srcset: {sources[0].get('srcset', 'N/A')[:100]}")
        if imgs:
            print(f"   Img src: {imgs[0].get('src', 'N/A')[:100]}")
        print()
    
    # Find cards and their surrounding structure
    print("\n" + "="*80)
    print("CARD STRUCTURE")
    print("="*80)
    cards = soup.find_all("a", {"data-testid": "listing-card-content"})
    if cards:
        card = cards[0]
        print(f"First card href: {card.get('href')}")
        print(f"\nCard parent: {card.parent.name if card.parent else 'None'}")
        print(f"Card parent class: {card.parent.get('class') if card.parent else 'None'}")
        
        # Check if there's an image in the parent or grandparent
        parent = card.parent
        for level in range(5):
            if parent:
                imgs_in_parent = parent.find_all("img", recursive=False)
                pics_in_parent = parent.find_all("picture", recursive=False)
                print(f"\nLevel {level} parent ({parent.name}):")
                print(f"  Class: {parent.get('class')}")
                print(f"  Direct img children: {len(imgs_in_parent)}")
                print(f"  Direct picture children: {len(pics_in_parent)}")
                
                if imgs_in_parent:
                    print(f"  First img src: {imgs_in_parent[0].get('src', 'N/A')[:80]}")
                if pics_in_parent:
                    print(f"  Picture found!")
                    
                parent = parent.parent
            else:
                break
    
    # Check if images are in a sibling element
    print("\n" + "="*80)
    print("CHECKING SIBLINGS")
    print("="*80)
    if cards:
        card = cards[0]
        # Check previous and next siblings
        prev_sib = card.find_previous_sibling()
        next_sib = card.find_next_sibling()
        
        print(f"Previous sibling: {prev_sib.name if prev_sib else 'None'}")
        if prev_sib:
            print(f"  Class: {prev_sib.get('class')}")
            imgs = prev_sib.find_all("img")
            print(f"  Images in prev sibling: {len(imgs)}")
            if imgs:
                print(f"  First img: {imgs[0].get('src', 'N/A')[:80]}")
        
        print(f"\nNext sibling: {next_sib.name if next_sib else 'None'}")
        if next_sib:
            print(f"  Class: {next_sib.get('class')}")

if __name__ == "__main__":
    asyncio.run(find_zoopla_images())
