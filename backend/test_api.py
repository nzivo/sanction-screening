"""
Test script to verify the sanctions screening system
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_screen_name():
    """Test screening a name"""
    print("\n=== Testing Name Screening ===")
    
    data = {
        "name": "William Ruto",
        "entity_type": "Individual",
        "country": "Kenya",
        "include_pep": True,
        "include_sanctions": True
    }
    
    response = requests.post(f"{BASE_URL}/screen", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    
    print(f"\nQuery: {result['query_name']}")
    print(f"Total Matches: {result['total_matches']}")
    print(f"Highest Score: {result['highest_score']}")
    
    if result['pep_matches']:
        print(f"\nPEP Matches:")
        for match in result['pep_matches'][:3]:  # Show first 3
            print(f"  - {match['matched_name']} ({match['match_score']}%)")
            print(f"    Position: {match.get('position', 'N/A')}")
    
    if result['sanctions_matches']:
        print(f"\nSanctions Matches:")
        for match in result['sanctions_matches'][:3]:
            print(f"  - {match['matched_name']} ({match['match_score']}%)")
            print(f"    Source: {match['source']}")


def test_batch_screen():
    """Test batch screening"""
    print("\n=== Testing Batch Screening ===")
    
    data = {
        "names": [
            "William Ruto",
            "Martha Koome",
            "Johnson Sakaja"
        ],
        "country": "Kenya",
        "include_pep": True,
        "include_sanctions": False
    }
    
    response = requests.post(f"{BASE_URL}/screen/batch", json=data)
    print(f"Status: {response.status_code}")
    results = response.json()
    
    print(f"\nScreened {len(results['results'])} names:")
    for result in results['results']:
        print(f"  - {result['query_name']}: {result['total_matches']} matches")


def test_get_peps():
    """Test getting PEPs by country"""
    print("\n=== Testing Get PEPs by Country ===")
    
    response = requests.get(f"{BASE_URL}/pep/country/Kenya")
    print(f"Status: {response.status_code}")
    peps = response.json()
    
    print(f"\nFound {len(peps)} PEPs in Kenya")
    for pep in peps[:5]:  # Show first 5
        print(f"  - {pep['full_name']}")
        print(f"    Position: {pep['position']}")
        print(f"    Risk Level: {pep['risk_level']}")


def test_add_pep():
    """Test adding a new PEP"""
    print("\n=== Testing Add PEP ===")
    
    data = {
        "country": "Kenya",
        "full_name": "Test Person",
        "position": "Test Minister",
        "position_level": "National",
        "organization": "Ministry of Testing",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "Medium"
    }
    
    response = requests.post(f"{BASE_URL}/pep", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_lists_status():
    """Test getting sanctions lists status"""
    print("\n=== Testing Lists Status ===")
    
    response = requests.get(f"{BASE_URL}/lists/status")
    print(f"Status: {response.status_code}")
    status = response.json()
    
    print(f"\nList Counts:")
    for source, count in status.get('list_counts', {}).items():
        print(f"  - {source}: {count} entries")
    
    print(f"\nRecent Updates:")
    for update in status.get('recent_updates', [])[:3]:
        print(f"  - {update['source']} ({update['list_type']}): {update['status']}")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Sanctions Screening System - Test Suite")
    print("=" * 60)
    
    try:
        test_health()
        test_get_peps()
        test_screen_name()
        test_batch_screen()
        test_lists_status()
        # test_add_pep()  # Uncomment to test adding a PEP
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Make sure the API server is running at http://localhost:8000")


if __name__ == "__main__":
    run_all_tests()
