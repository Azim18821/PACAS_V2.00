"""
Test lead capture functionality
"""
import requests

BASE_URL = "http://127.0.0.1:5000"

def test_lead_capture():
    """Test capturing a lead"""
    print("Testing lead capture...")
    
    lead_data = {
        "email": "test@example.com",
        "property_url": "https://www.rightmove.co.uk/properties/123456",
        "property_title": "Test Property, Manchester",
        "property_price": "£1,500 pcm",
        "site": "Rightmove"
    }
    
    response = requests.post(f"{BASE_URL}/api/capture-lead", json=lead_data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✓ Lead captured successfully!")
    else:
        print("✗ Failed to capture lead")

def test_leads_stats():
    """Test getting lead statistics"""
    print("\nTesting leads stats...")
    
    response = requests.get(f"{BASE_URL}/api/admin/leads/stats")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_get_leads():
    """Test retrieving leads"""
    print("\nTesting get leads...")
    
    response = requests.get(f"{BASE_URL}/api/admin/leads?limit=5")
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total leads: {data.get('count', 0)}")
    
    if data.get('leads'):
        print("\nRecent leads:")
        for lead in data['leads'][:3]:
            print(f"  - {lead['email']} clicked {lead['site']} property")
            print(f"    {lead['property_title']} - {lead['property_price']}")
            print(f"    Time: {lead['timestamp']}")

if __name__ == "__main__":
    test_lead_capture()
    test_leads_stats()
    test_get_leads()
    
    print("\n✓ All tests completed!")
    print("\nNext steps:")
    print("1. Open http://127.0.0.1:5000 in browser")
    print("2. Search for properties")
    print("3. Click 'View Details' on a property")
    print("4. Enter email in popup")
    print("5. Check leads at /api/admin/leads")
