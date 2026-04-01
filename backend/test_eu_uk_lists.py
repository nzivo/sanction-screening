"""
Test script for EU and UK sanctions list downloaders
Run this after starting the FastAPI server to test the new endpoints
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test if API is running"""
    print("\n=== Testing API Health ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✓ API is healthy: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ API is not running: {e}")
        print("  Please start the server with: python main.py")
        return False

def test_update_eu_list():
    """Test EU list update endpoint"""
    print("\n=== Testing EU List Update ===")
    try:
        response = requests.post(f"{BASE_URL}/lists/update/eu")
        result = response.json()
        print(f"✓ EU update triggered: {result['message']}")
        print(f"  Source: {result['source']}")
        print(f"  List Type: {result['list_type']}")
        return True
    except Exception as e:
        print(f"✗ EU update failed: {e}")
        return False

def test_update_uk_list():
    """Test UK list update endpoint"""
    print("\n=== Testing UK List Update ===")
    try:
        response = requests.post(f"{BASE_URL}/lists/update/uk")
        result = response.json()
        print(f"✓ UK update triggered: {result['message']}")
        print(f"  Source: {result['source']}")
        print(f"  List Type: {result['list_type']}")
        return True
    except Exception as e:
        print(f"✗ UK update failed: {e}")
        return False

def test_update_all_lists():
    """Test update all lists endpoint"""
    print("\n=== Testing Update All Lists ===")
    try:
        response = requests.post(f"{BASE_URL}/lists/update/all")
        result = response.json()
        print(f"✓ All lists update triggered: {result['message']}")
        print(f"  Lists: {', '.join(result['lists'])}")
        return True
    except Exception as e:
        print(f"✗ Update all failed: {e}")
        return False

def test_list_status():
    """Check status of all lists"""
    print("\n=== Checking List Status ===")
    try:
        response = requests.get(f"{BASE_URL}/lists/status")
        result = response.json()
        print(f"✓ List status retrieved:")
        print(json.dumps(result, indent=2))
        return True
    except Exception as e:
        print(f"✗ Status check failed: {e}")
        return False

def test_screening():
    """Test screening against all lists"""
    print("\n=== Testing Screening ===")
    try:
        # Test with a known sanctioned name
        test_name = "Vladimir Putin"
        response = requests.post(
            f"{BASE_URL}/screen",
            json={
                "name": test_name,
                "entity_type": "Individual",
                "include_sanctions": True,
                "include_pep": False
            }
        )
        result = response.json()
        print(f"✓ Screening completed for '{test_name}'")
        print(f"  Total matches: {result['total_matches']}")
        print(f"  Highest score: {result['highest_score']}")
        
        if result['sanctions_matches']:
            print(f"\n  Match sources:")
            sources = {}
            for match in result['sanctions_matches']:
                source = match['source']
                if source not in sources:
                    sources[source] = 0
                sources[source] += 1
            
            for source, count in sources.items():
                print(f"    - {source}: {count} match(es)")
        
        return True
    except Exception as e:
        print(f"✗ Screening failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("EU & UK Sanctions Lists - Test Suite")
    print("=" * 60)
    
    # Check if API is running
    if not test_health():
        return
    
    # Run tests
    results = []
    results.append(("Health Check", test_health()))
    results.append(("EU List Update", test_update_eu_list()))
    results.append(("UK List Update", test_update_uk_list()))
    results.append(("Update All Lists", test_update_all_lists()))
    
    # Wait a bit for background tasks
    print("\n⏳ Waiting 5 seconds for background updates to process...")
    time.sleep(5)
    
    results.append(("List Status", test_list_status()))
    results.append(("Screening Test", test_screening()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
