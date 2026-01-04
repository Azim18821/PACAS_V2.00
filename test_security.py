"""
Test script to validate security improvements
"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

def test_health_endpoint():
    """Test health check endpoint"""
    print("\n1. Testing Health Check Endpoint...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ API Status: {data['status']}")
        print(f"   ✓ Daily Usage: {data['api_usage']['daily_requests']}/{data['api_usage']['daily_limit']}")
        print(f"   ✓ Hourly Usage: {data['api_usage']['hourly_requests']}/{data['api_usage']['hourly_limit']}")
    else:
        print(f"   ✗ Failed: {response.text}")

def test_input_sanitization():
    """Test input sanitization"""
    print("\n2. Testing Input Sanitization...")
    
    # Test with malicious input
    malicious_inputs = [
        {"location": "<script>alert('xss')</script>", "site": "zoopla"},
        {"location": "'; DROP TABLE listings; --", "site": "zoopla"},
        {"location": "Manchester" * 50, "site": "zoopla"},  # Very long input
    ]
    
    for i, payload in enumerate(malicious_inputs, 1):
        print(f"\n   Test {i}: {payload['location'][:50]}...")
        response = requests.post(
            f"{BASE_URL}/api/search",
            json=payload
        )
        if response.status_code in [400, 429]:
            print(f"   ✓ Blocked malicious input (Status: {response.status_code})")
        else:
            print(f"   Status: {response.status_code}")

def test_rate_limiting():
    """Test rate limiting"""
    print("\n3. Testing Rate Limiting...")
    print("   Sending 12 requests rapidly (limit is 10/min)...")
    
    search_payload = {
        "site": "zoopla",
        "location": "London",
        "min_price": "100000",
        "max_price": "500000",
        "listing_type": "sale"
    }
    
    success_count = 0
    rate_limited_count = 0
    
    for i in range(12):
        response = requests.post(
            f"{BASE_URL}/api/search",
            json=search_payload
        )
        if response.status_code == 429:
            rate_limited_count += 1
            print(f"   Request {i+1}: Rate limited ✓")
            break
        elif response.status_code in [200, 400]:
            success_count += 1
            print(f"   Request {i+1}: Success", end="")
            if i == 9:
                print(" (limit approaching)")
            else:
                print()
        time.sleep(0.1)
    
    if rate_limited_count > 0:
        print(f"\n   ✓ Rate limiting working! {success_count} succeeded, then blocked")
    else:
        print(f"\n   ⚠ Warning: Rate limit not triggered after {success_count} requests")

def test_price_validation():
    """Test price range validation"""
    print("\n4. Testing Price Validation...")
    
    # Test excessive price
    excessive_price = {
        "site": "zoopla",
        "location": "London",
        "min_price": "0",
        "max_price": "100000000",  # 100 million (should be rejected)
        "listing_type": "sale"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/search",
        json=excessive_price
    )
    
    if response.status_code == 400 and "exceed" in response.text.lower():
        print("   ✓ Excessive price rejected")
    else:
        print(f"   Status: {response.status_code}")

def test_cors_headers():
    """Test CORS configuration"""
    print("\n5. Testing CORS Headers...")
    response = requests.options(
        f"{BASE_URL}/api/search",
        headers={"Origin": "http://example.com"}
    )
    
    if 'Access-Control-Allow-Origin' in response.headers:
        print(f"   ✓ CORS enabled: {response.headers['Access-Control-Allow-Origin']}")
    else:
        print("   ✗ CORS not configured")

def run_all_tests():
    """Run all security tests"""
    print("=" * 60)
    print("PACAS Security Test Suite")
    print("=" * 60)
    
    try:
        # Check if server is running
        try:
            requests.get(BASE_URL, timeout=2)
        except requests.exceptions.ConnectionError:
            print("\n❌ Error: Flask server not running!")
            print("   Please start the server with: py main.py")
            return
        
        test_health_endpoint()
        test_input_sanitization()
        test_rate_limiting()
        test_price_validation()
        test_cors_headers()
        
        print("\n" + "=" * 60)
        print("✅ Security test suite completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")

if __name__ == "__main__":
    run_all_tests()
