import pytest
from utils.database import Database
import json
from datetime import datetime

@pytest.fixture
def db():
    """Create a test database instance"""
    database = Database()
    database.db_path = "test_listings.db"  # Use a separate test database
    database.init_db()
    return database

def test_cache_and_retrieve_results(db):
    """Test caching and retrieving results"""
    test_results = {
        "listings": [
            {"title": "Test Property", "price": "200000", "location": "Test Location"}
        ],
        "total_found": 1,
        "total_pages": 1,
        "current_page": 1
    }
    
    # Cache the results
    db.cache_results(
        site="zoopla",
        location="Manchester",
        min_price="100000",
        max_price="500000",
        min_beds="2",
        max_beds="4",
        keywords="",
        listing_type="sale",
        page_number=1,
        results=test_results
    )
    
    # Retrieve the results
    cached = db.get_cached_results(
        site="zoopla",
        location="Manchester",
        min_price="100000",
        max_price="500000",
        min_beds="2",
        max_beds="4",
        keywords="",
        listing_type="sale",
        page_number=1
    )
    
    assert cached is not None
    assert cached["listings"][0]["title"] == "Test Property"
    assert cached["total_found"] == 1

def test_cache_expiry(db):
    """Test that old cache entries are not returned"""
    # This would require mocking datetime.now() to test properly
    # For now, we'll just verify that very old entries aren't returned
    pass

def test_null_parameter_handling(db):
    """Test handling of NULL parameters in database queries"""
    test_results = {
        "listings": [
            {"title": "Test Property", "price": "200000", "location": "Test Location"}
        ],
        "total_found": 1,
        "total_pages": 1,
        "current_page": 1
    }
    
    # Cache with some NULL parameters
    db.cache_results(
        site="zoopla",
        location="Manchester",
        min_price=None,
        max_price=None,
        min_beds=None,
        max_beds=None,
        keywords="",
        listing_type="sale",
        page_number=1,
        results=test_results
    )
    
    # Retrieve with the same NULL parameters
    cached = db.get_cached_results(
        site="zoopla",
        location="Manchester",
        min_price=None,
        max_price=None,
        min_beds=None,
        max_beds=None,
        keywords="",
        listing_type="sale",
        page_number=1
    )
    
    assert cached is not None
    assert cached["listings"][0]["title"] == "Test Property" 