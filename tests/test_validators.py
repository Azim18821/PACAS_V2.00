import pytest
from utils.validators import validate_location, validate_price_range, validate_bed_range, ValidationError

def test_validate_location_valid_city():
    """Test validation of valid city names"""
    assert validate_location("London") == "London"
    assert validate_location("Manchester") == "Manchester"
    assert validate_location("Birmingham") == "Birmingham"

def test_validate_location_valid_postcode():
    """Test validation of valid postcodes"""
    assert validate_location("M40") == "M40"
    assert validate_location("SW1") == "SW1"

def test_validate_location_invalid():
    """Test validation of invalid locations"""
    with pytest.raises(ValidationError):
        validate_location("")  # Empty location
    with pytest.raises(ValidationError):
        validate_location("123")  # Invalid postcode format
    with pytest.raises(ValidationError):
        validate_location("InvalidCity123")  # Invalid city name

def test_validate_price_range():
    """Test price range validation"""
    min_price, max_price = validate_price_range("100000", "500000", "sale")
    assert min_price == "100000"
    assert max_price == "500000"

    # Test invalid price range
    with pytest.raises(ValidationError):
        validate_price_range("500000", "100000", "sale")  # min > max

def test_validate_bed_range():
    """Test bed range validation"""
    min_beds, max_beds = validate_bed_range("2", "4")
    assert min_beds == 2
    assert max_beds == 4

    # Test invalid bed range
    with pytest.raises(ValidationError):
        validate_bed_range("4", "2")  # min > max 