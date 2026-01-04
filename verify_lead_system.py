"""
Quick verification of lead capture system
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

print("=" * 60)
print("LEAD CAPTURE SYSTEM VERIFICATION")
print("=" * 60)

# Test 1: Health Check
print("\n1. Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/health")
    if response.status_code == 200:
        print("   ✅ Health check passed")
        data = response.json()
        print(f"   Status: {data['status']}")
    else:
        print(f"   ❌ Health check failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Capture a lead
print("\n2. Testing lead capture...")
try:
    lead_data = {
        "email": "test@example.com",
        "property_url": "https://www.rightmove.co.uk/properties/12345",
        "property_title": "2 Bed Flat, Manchester",
        "property_price": "£1,500 pcm",
        "site": "Rightmove"
    }
    response = requests.post(f"{BASE_URL}/api/capture-lead", json=lead_data)
    if response.status_code == 200:
        print("   ✅ Lead captured successfully")
        print(f"   Response: {response.json()}")
    else:
        print(f"   ❌ Lead capture failed: {response.status_code}")
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Get lead stats
print("\n3. Testing lead statistics...")
try:
    response = requests.get(f"{BASE_URL}/api/admin/leads/stats")
    if response.status_code == 200:
        print("   ✅ Stats retrieved successfully")
        stats = response.json()
        print(f"   Total leads: {stats.get('total_leads', 0)}")
        print(f"   Unique emails: {stats.get('unique_emails', 0)}")
        print(f"   By site: {stats.get('by_site', {})}")
        print(f"   Today: {stats.get('today', 0)}")
    else:
        print(f"   ❌ Stats failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Get recent leads
print("\n4. Testing leads retrieval...")
try:
    response = requests.get(f"{BASE_URL}/api/admin/leads?limit=5")
    if response.status_code == 200:
        print("   ✅ Leads retrieved successfully")
        data = response.json()
        print(f"   Found {data['count']} leads")
        if data['leads']:
            print("\n   Recent leads:")
            for i, lead in enumerate(data['leads'][:3], 1):
                print(f"   {i}. {lead['email']} - {lead['site']} - {lead['property_price']}")
    else:
        print(f"   ❌ Leads retrieval failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Test rate limiting
print("\n5. Testing rate limiting (capture endpoint)...")
try:
    success_count = 0
    for i in range(25):
        response = requests.post(f"{BASE_URL}/api/capture-lead", json={
            "email": f"test{i}@example.com",
            "property_url": "https://test.com",
            "site": "Test"
        })
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            print(f"   ✅ Rate limit triggered after {success_count} requests")
            break
    else:
        print(f"   ⚠️  Rate limit not triggered (captured {success_count} leads)")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
print("\n📊 View your leads dashboard:")
print(f"   {BASE_URL}/api/admin/leads")
print(f"\n📈 View statistics:")
print(f"   {BASE_URL}/api/admin/leads/stats")
print(f"\n💾 Export to CSV:")
print(f"   {BASE_URL}/api/admin/leads/export")
print("\n🌐 Test the frontend:")
print(f"   {BASE_URL}")
print("   (Search properties and click 'View Details' to see the email popup)")
print("=" * 60)
