import os
import random
from dotenv import load_dotenv
from utils.logger import logger

# Load environment variables
load_dotenv()

class ProxyRotator:
    def __init__(self):
        self.scraper_api_key = os.getenv("SCRAPER_API_KEY")
        self.brightdata_key = os.getenv("BRIGHTDATA_KEY")
        self.scrapingbee_key = os.getenv("SCRAPINGBEE_KEY")
        self.proxy_scrape_key = os.getenv("PROXY_SCRAPE_KEY")
        
        # Initialize available scrapers
        self.scrapers = []
        if self.scraper_api_key:
            self.scrapers.append("scraperapi")
        if self.brightdata_key:
            self.scrapers.append("brightdata")
        if self.scrapingbee_key:
            self.scrapers.append("scrapingbee")
        if self.proxy_scrape_key:
            self.scrapers.append("proxyscrape")
            
        if not self.scrapers:
            logger.error("No scraping services configured. Please add API keys to .env file")
            raise ValueError("No scraping services available")

    def get_proxy_url(self, url):
        """Get a proxy URL using a randomly selected scraping service"""
        if not self.scrapers:
            logger.error("No scraping services available")
            return url
            
        # Randomly select a scraper
        scraper = random.choice(self.scrapers)
        
        try:
            if scraper == "scraperapi":
                return f"http://api.scraperapi.com?api_key={self.scraper_api_key}&url={url}"
            elif scraper == "brightdata":
                return f"http://brd.superproxy.io:22225?api_key={self.brightdata_key}&url={url}"
            elif scraper == "scrapingbee":
                return f"https://app.scrapingbee.com/api/v1/?api_key={self.scrapingbee_key}&url={url}"
            elif scraper == "proxyscrape":
                return f"https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&url={url}"
            else:
                logger.error(f"Unknown scraper service: {scraper}")
                return url
        except Exception as e:
            logger.error(f"Error generating proxy URL for {scraper}: {str(e)}")
            # If one service fails, try another
            self.scrapers.remove(scraper)
            if self.scrapers:
                return self.get_proxy_url(url)
            return url

    def get_available_scrapers(self):
        """Return list of available scraping services"""
        return self.scrapers.copy()

    def remove_scraper(self, scraper):
        """Remove a scraper from the rotation if it's failing"""
        if scraper in self.scrapers:
            self.scrapers.remove(scraper)
            logger.warning(f"Removed {scraper} from rotation due to failures") 