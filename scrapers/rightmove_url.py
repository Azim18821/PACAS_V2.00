from urllib.parse import urlencode

# ✅ Correct Rightmove region codes (same for sale and rent in these cities)
REGION_IDS = {
    "london": ("London", {
        "sale": "REGION^87490",
        "rent": "REGION^87490"
    }),
    "manchester": ("Manchester, Greater Manchester", {
        "sale": "REGION^904",
        "rent": "REGION^904"
    }),
    "birmingham": ("Birmingham, West Midlands", {
        "sale": "REGION^946",
        "rent": "REGION^946"
    }),
    "leeds": ("Leeds, West Yorkshire", {
        "sale": "REGION^918",
        "rent": "REGION^918"
    }),
    # Add more if needed
}

# Sorting options for Rightmove
SORT_OPTIONS = {
    "newest": "0",  # Newest Listed
    "price_asc": "1",  # Price (Low to High)
    "price_desc": "2",  # Price (High to Low)
    "beds_desc": "3",  # Bedrooms (High to Low)
    "beds_asc": "4",  # Bedrooms (Low to High)
    "oldest": "5",  # Oldest Listed
    "distance": "6",  # Distance
    "reduced": "7",  # Price Reduced
    "most_viewed": "8",  # Most Viewed
    "most_reduced": "9"  # Most Reduced
}

def get_final_rightmove_results_url(
    location,
    min_price="",
    max_price="",
    min_beds="",
    max_beds="",
    radius="0.0",
    include_sold=True,
    listing_type="sale",  # "sale" or "rent"
    sort_by="newest",  # Default to newest listings
    page=1  # Add page parameter
):
    try:
        key = location.strip().lower()
        if key not in REGION_IDS:
            print("[Rightmove URL] Location not recognised:", location)
            return None

        display_text, ids = REGION_IDS[key]
        location_id = ids.get(listing_type)
        if not location_id:
            print("[Rightmove URL] No ID for listing type:", listing_type)
            return None

        if listing_type == "rent":
            base_url = "https://www.rightmove.co.uk/property-to-rent/find.html"
        else:
            base_url = "https://www.rightmove.co.uk/property-for-sale/find.html"

        # Convert price values to strings and remove decimal points
        def clean_price(price):
            if price is None:
                return ""
            try:
                # Convert to float first to handle any numeric input
                price_float = float(price)
                # Convert to integer to remove decimal points
                price_int = int(price_float)
                return str(price_int)
            except (ValueError, TypeError):
                return str(price)

        min_price = clean_price(min_price)
        max_price = clean_price(max_price)
        min_beds = str(min_beds) if min_beds is not None else ""
        max_beds = str(max_beds) if max_beds is not None else ""

        params = {
            "searchLocation": display_text,
            "useLocationIdentifier": "true",
            "locationIdentifier": location_id,
            "radius": radius,
            "minPrice": min_price,
            "maxPrice": max_price,
            "minBedrooms": min_beds,
            "maxBedrooms": max_beds,
            "sortType": SORT_OPTIONS.get(sort_by, "0")  # Add sort type
        }

        # Add pagination parameters for both sale and rent
        if page > 1:
            # For page 2, index should be 24, for page 3 it should be 48, etc.
            index = (page - 1) * 24
            params["index"] = str(index)
            # Add displayLocationIdentifier for better pagination handling
            params["displayLocationIdentifier"] = display_text.replace(" ", "").replace(",", "").replace("+", "")

        if listing_type == "sale":
            params["_includeSSTC"] = "on" if include_sold else "off"
        elif listing_type == "rent":
            # Add rental-specific parameters
            params["_includeLetAgreed"] = "on"
            params["channel"] = "RENT"
            params["transactionType"] = "LETTING"

        full_url = base_url + "?" + urlencode(params)
        print("[Rightmove URL] Generated:", full_url)
        return full_url

    except Exception as e:
        print("[Rightmove URL ERROR]", e)
        return None
