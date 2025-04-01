import pytest
import asyncio
from main import app
from flask.testing import FlaskClient
from werkzeug.test import TestResponse
import json

class AsyncTestClient(FlaskClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    app.test_client_class = AsyncTestClient
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_scraper_response():
    """Mock response for scraper functions"""
    return {
        "listings": [
            {
                "title": "Test Property 1",
                "price": "250000",
                "location": "Manchester",
                "description": "A test property",
                "bedrooms": "3",
                "url": "http://test.com/property1"
            },
            {
                "title": "Test Property 2",
                "price": "300000",
                "location": "Manchester",
                "description": "Another test property",
                "bedrooms": "4",
                "url": "http://test.com/property2"
            }
        ],
        "total_found": 2,
        "total_pages": 1,
        "current_page": 1,
        "has_next_page": False
    } 