"""
Security utilities for rate limiting and API protection
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from utils.logger import logger

class ScraperAPIMonitor:
    """Monitor ScraperAPI usage to prevent cost overruns"""
    
    def __init__(self):
        self.requests_today = 0
        self.last_reset = datetime.now().date()
        # Default limits from environment or use safe defaults
        self.daily_limit = int(os.getenv('MAX_REQUESTS_PER_DAY', '1000'))
        self.hourly_limit = int(os.getenv('MAX_REQUESTS_PER_HOUR', '100'))
        self.hourly_requests = []
        
    def check_limits(self) -> tuple[bool, Optional[str]]:
        """Check if we're within usage limits"""
        # Reset daily counter if it's a new day
        today = datetime.now().date()
        if today > self.last_reset:
            self.requests_today = 0
            self.last_reset = today
            logger.info("ScraperAPI daily counter reset")
        
        # Check daily limit
        if self.requests_today >= self.daily_limit:
            logger.warning(f"Daily ScraperAPI limit reached: {self.requests_today}/{self.daily_limit}")
            return False, f"Daily API limit reached ({self.daily_limit} requests). Try again tomorrow."
        
        # Check hourly limit
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        self.hourly_requests = [req for req in self.hourly_requests if req > one_hour_ago]
        
        if len(self.hourly_requests) >= self.hourly_limit:
            logger.warning(f"Hourly ScraperAPI limit reached: {len(self.hourly_requests)}/{self.hourly_limit}")
            return False, f"Hourly API limit reached ({self.hourly_limit} requests). Try again later."
        
        return True, None
    
    def record_request(self):
        """Record a new API request"""
        self.requests_today += 1
        self.hourly_requests.append(datetime.now())
        logger.info(f"ScraperAPI request recorded. Daily: {self.requests_today}, Hourly: {len(self.hourly_requests)}")
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        hourly_count = len([req for req in self.hourly_requests if req > one_hour_ago])
        
        return {
            'daily_requests': self.requests_today,
            'daily_limit': self.daily_limit,
            'hourly_requests': hourly_count,
            'hourly_limit': self.hourly_limit,
            'daily_remaining': self.daily_limit - self.requests_today,
            'hourly_remaining': self.hourly_limit - hourly_count
        }

# Global instance
scraper_api_monitor = ScraperAPIMonitor()


def get_client_ip(request) -> str:
    """Get the real client IP address, handling proxies"""
    # Check for common proxy headers
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


def sanitize_location(location: str) -> str:
    """Sanitize location input to prevent injection attacks"""
    if not location:
        return ""
    
    # Remove any suspicious characters
    # Allow letters, numbers, spaces, hyphens, commas, apostrophes
    import re
    sanitized = re.sub(r'[^a-zA-Z0-9\s\-,\']', '', location)
    
    # Limit length to prevent abuse
    max_length = 100
    if len(sanitized) > max_length:
        logger.warning(f"Location truncated from {len(sanitized)} to {max_length} chars")
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def validate_price_limits(min_price: int, max_price: int) -> tuple[bool, Optional[str]]:
    """Validate price ranges to prevent excessive queries"""
    # Maximum allowed price to prevent abuse
    MAX_PRICE = 50_000_000  # 50 million
    
    if max_price > MAX_PRICE:
        logger.warning(f"Price exceeds maximum: {max_price}")
        return False, f"Maximum price cannot exceed £{MAX_PRICE:,}"
    
    # Prevent extremely wide ranges that could cause performance issues
    if max_price > 0 and (max_price - min_price) > 40_000_000:
        logger.warning(f"Price range too wide: {min_price} - {max_price}")
        return False, "Price range is too wide. Please narrow your search."
    
    return True, None
