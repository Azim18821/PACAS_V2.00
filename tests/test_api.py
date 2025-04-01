import pytest
from main import app
import json
from unittest.mock import patch, AsyncMock

pytestmark = pytest.mark.asyncio

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.mark.asyncio
async def test_search_endpoint_valid_request(test_client, mock_scraper_response):
    """Test search endpoint with valid parameters"""
    with patch('main.scrape_zoopla_first_page', new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = (mock_scraper_response["listings"], 1)
        data = {
            "site": "zoopla",
            "location": "Manchester",
            "listing_type": "sale",
            "min_price": "100000",
            "max_price": "500000",
            "min_beds": "2",
            "max_beds": "4",
            "keywords": ""
        }
        
        response = await test_client.post('/api/search',
                                data=json.dumps(data),
                                content_type='application/json')
        assert response.status_code == 200
        json_data = json.loads(response.data)
        assert "listings" in json_data
        assert len(json_data["listings"]) == 2
        assert json_data["listings"][0]["title"] == "Test Property 1"

@pytest.mark.asyncio
async def test_search_endpoint_invalid_request(test_client):
    """Test search endpoint with invalid parameters"""
    data = {
        "site": "zoopla",
        "location": "",  # Empty location should fail
        "listing_type": "sale",
        "min_price": "100000",
        "max_price": "500000",
        "min_beds": "2",
        "max_beds": "4",
        "keywords": ""
    }
    
    response = await test_client.post('/api/search',
                            data=json.dumps(data),
                            content_type='application/json')
    assert response.status_code == 400
    json_data = json.loads(response.data)
    assert "error" in json_data
    assert "location" in json_data["error"].lower()

@pytest.mark.asyncio
async def test_next_page_endpoint(test_client, mock_scraper_response):
    """Test next page endpoint"""
    with patch('main.scrape_zoopla_first_page', new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = (mock_scraper_response["listings"], 2)
        data = {
            "search_params": {
                "site": "zoopla",
                "location": "Manchester",
                "listing_type": "sale",
                "min_price": "100000",
                "max_price": "500000",
                "min_beds": "2",
                "max_beds": "4",
                "keywords": ""
            },
            "current_page": 2
        }
        
        response = await test_client.post('/api/search/next-page',
                                data=json.dumps(data),
                                content_type='application/json')
        assert response.status_code == 200
        json_data = json.loads(response.data)
        assert "listings" in json_data
        assert len(json_data["listings"]) == 2

@pytest.mark.asyncio
async def test_rate_limiting(test_client):
    """Test rate limiting functionality"""
    data = {
        "site": "zoopla",
        "location": "Manchester",
        "listing_type": "sale",
        "min_price": "100000",
        "max_price": "500000",
        "min_beds": "2",
        "max_beds": "4",
        "keywords": ""
    }
    
    responses = []
    for _ in range(105):  # Exceed the rate limit (100 requests per hour)
        response = await test_client.post('/api/search',
                                data=json.dumps(data),
                                content_type='application/json')
        responses.append(response.status_code)
    
    assert 429 in responses  # HTTP 429 Too Many Requests

@pytest.mark.asyncio
async def test_cache_usage(test_client, mock_scraper_response):
    """Test that results are properly cached and reused"""
    with patch('main.scrape_zoopla_first_page', new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = (mock_scraper_response["listings"], 1)
        data = {
            "site": "zoopla",
            "location": "Manchester",
            "listing_type": "sale",
            "min_price": "100000",
            "max_price": "500000",
            "min_beds": "2",
            "max_beds": "4",
            "keywords": ""
        }
        
        # First request should hit the scraper
        response1 = await test_client.post('/api/search',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        # Second request with same parameters should use cache
        response2 = await test_client.post('/api/search',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert mock_scrape.call_count == 1  # Scraper should only be called once 