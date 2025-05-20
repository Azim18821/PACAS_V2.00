from typing import Dict, Any, Tuple
from datetime import datetime, timedelta
from functools import wraps
import time
import re
from utils.logger import logger

class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

# UK Postcode patterns
FULL_POSTCODE_PATTERN = re.compile(r'^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$')
OUTWARD_CODE_PATTERN = re.compile(r'^[A-Z]{1,2}[0-9][A-Z0-9]?$')

def is_valid_postcode(postcode: str) -> bool:
    """Check if a string is a valid UK postcode format (full or outward code)."""
    # Convert to uppercase and remove extra spaces
    postcode = postcode.upper().strip()
    # Check if it matches either the full postcode or outward code pattern
    return bool(FULL_POSTCODE_PATTERN.match(postcode) or OUTWARD_CODE_PATTERN.match(postcode))

# List of valid UK locations (major cities and areas)
VALID_LOCATIONS = [
    # London areas
    'London', 'Central London', 'North London', 'South London', 'East London', 'West London',
    'Camden', 'Kensington', 'Chelsea', 'Westminster', 'Greenwich', 'Richmond', 'Hackney',
    
    # Major cities
    'Manchester', 'Liverpool', 'Birmingham', 'Leeds', 'Glasgow', 'Edinburgh', 'Cardiff',
    'Bristol', 'Sheffield', 'Nottingham', 'Leicester', 'Coventry', 'Hull', 'Newcastle',
    
    # Areas around major cities
    'Greater Manchester', 'Merseyside', 'West Midlands', 'West Yorkshire', 'Greater Glasgow',
    'Lothian', 'South Gloucestershire', 'South Yorkshire', 'Nottinghamshire', 'Leicestershire',
    
    # Other major areas
    'Brighton', 'Bath', 'Oxford', 'Cambridge', 'York', 'Belfast', 'Aberdeen', 'Dundee',
    'Exeter', 'Plymouth', 'Southampton', 'Portsmouth', 'Norwich', 'Leicester', 'Derby',
    
    # Counties
    'Surrey', 'Kent', 'Essex', 'Hertfordshire', 'Buckinghamshire', 'Berkshire', 'Hampshire',
    'Sussex', 'Devon', 'Cornwall', 'Somerset', 'Dorset', 'Wiltshire', 'Gloucestershire',
    'Worcestershire', 'Warwickshire', 'Staffordshire', 'Cheshire', 'Lancashire', 'Yorkshire',
    'Durham', 'Northumberland', 'Cumbria', 'Wales', 'Scotland', 'Northern Ireland'
]

def validate_price_range(min_price: str, max_price: str, listing_type: str = "sale", site: str = "zoopla") -> Tuple[str, str]:
    """Validate and convert price range to string values."""
    try:
        # Convert to float for validation only
        min_price_float = float(min_price) if min_price else 0
        max_price_float = float(max_price) if max_price else 10000000  # Default to 10M for all listings
        
        if min_price_float < 0:
            logger.error(f"Invalid minimum price: {min_price}")
            raise ValidationError("Minimum price cannot be negative", "min_price")
        if max_price_float < min_price_float:
            logger.error(f"Invalid price range: min={min_price}, max={max_price}")
            raise ValidationError("Maximum price must be greater than minimum price", "max_price")
        if listing_type == "rent" and site == "rightmove" and max_price_float > 20000:
            logger.warning(f"Price capped at 20K for Rightmove rentals: {max_price}")
            max_price_float = 20000
            
        # Convert to integers to remove decimal points, then to strings
        return str(int(min_price_float)), str(int(max_price_float))
    except ValueError as e:
        logger.error(f"Price format error: min={min_price}, max={max_price}")
        raise ValidationError("Invalid price format. Please enter valid numbers", "price")

def validate_bed_range(min_beds: str, max_beds: str) -> Tuple[int, int]:
    """Validate and convert bed range to integer values."""
    try:
        min_beds = int(min_beds) if min_beds else 0
        max_beds = int(max_beds) if max_beds else 10  # Use 10 instead of infinity
        
        if min_beds < 0:
            logger.error(f"Invalid minimum beds: {min_beds}")
            raise ValidationError("Minimum beds cannot be negative", "min_beds")
        if max_beds < min_beds:
            logger.error(f"Invalid bed range: min={min_beds}, max={max_beds}")
            raise ValidationError("Maximum beds must be greater than minimum beds", "max_beds")
            
        return min_beds, max_beds
    except ValueError as e:
        logger.error(f"Bed format error: min={min_beds}, max={max_beds}")
        raise ValidationError("Invalid bed format. Please enter whole numbers", "beds")

def validate_location(location: str) -> str:
    """Validate location string."""
    if not location or not location.strip():
        logger.error("Empty location provided")
        raise ValidationError("Please enter a location", "location")
    
    # Clean the location string
    location = location.strip()
    
    # First check if it's a postcode (before any other validation)
    if any(c.isdigit() for c in location):
        # If it contains numbers, treat it as a potential postcode
        if is_valid_postcode(location):
            logger.info(f"Valid postcode provided: {location}")
            return location.upper()  # Return uppercase for consistency
        else:
            logger.error(f"Invalid postcode format: {location}")
            raise ValidationError("Invalid postcode format", "location")
    
    # If no numbers present, validate as a city/area name
    if len(location) < 2:
        logger.error(f"Location too short: {location}")
        raise ValidationError("Location must be at least 2 characters", "location")
    
    # For city/area names, only allow letters, spaces, and commas
    if not all(c.isalpha() or c.isspace() or c == ',' for c in location):
        logger.error(f"Invalid location format: {location}")
        raise ValidationError("Location can only contain letters, spaces, and commas", "location")
    
    # Check if location is in valid locations list
    normalized_location = location.lower()
    is_valid = any(
        valid_loc.lower() == normalized_location or
        normalized_location in valid_loc.lower()
        for valid_loc in VALID_LOCATIONS
    )
    
    if not is_valid:
        logger.error(f"Invalid location: {location}")
        raise ValidationError(
            f"'{location}' is not a valid UK location. Please enter a valid city, area, county, or postcode.",
            "location"
        )
    
    return location

def validate_listing_type(listing_type: str) -> str:
    """Validate listing type."""
    valid_types = ["sale", "rent"]
    if listing_type not in valid_types:
        logger.error(f"Invalid listing type: {listing_type}")
        raise ValidationError(f"Invalid listing type. Must be one of: {', '.join(valid_types)}", "listing_type")
    return listing_type

def validate_search_params(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate all search parameters."""
    try:
        logger.info(f"Validating search parameters: {data}")
        
        location = validate_location(data.get("location", ""))
        listing_type = validate_listing_type(data.get("listing_type", "sale"))
        site = data.get("site", "zoopla")
        
        # Validate site option
        if site not in ["zoopla", "rightmove", "combined"]:
            raise ValidationError(f"Invalid site option: {site}. Must be one of: zoopla, rightmove, combined")
        
        min_price, max_price = validate_price_range(
            data.get("min_price", ""),
            data.get("max_price", ""),
            listing_type,
            site
        )
        
        min_beds, max_beds = validate_bed_range(
            data.get("min_beds", ""),
            data.get("max_beds", "")
        )
        
        validated_data = {
            "location": location,
            "min_price": min_price,
            "max_price": max_price,
            "min_beds": min_beds,
            "max_beds": max_beds,
            "listing_type": listing_type,
            "keywords": data.get("keywords", "").strip(),
            "site": site
        }
        
        logger.info(f"Validation successful: {validated_data}")
        return validated_data
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise ValidationError(f"Invalid search parameters: {str(e)}", e.field)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        raise ValidationError("An unexpected error occurred during validation")

# Rate limiting implementation
class RateLimiter:
    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}

    def is_rate_limited(self, ip: str) -> bool:
        now = time.time()
        if ip not in self.requests:
            self.requests[ip] = []
        
        # Remove old requests
        self.requests[ip] = [req_time for req_time in self.requests[ip] 
                           if now - req_time < self.time_window]
        
        # Check if rate limit is exceeded
        if len(self.requests[ip]) >= self.max_requests:
            return True
        
        # Add new request
        self.requests[ip].append(now)
        return False

# Create a global rate limiter instance
rate_limiter = RateLimiter() 