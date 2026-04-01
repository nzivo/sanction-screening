"""
Debug script to inspect OFAC XML structure
"""

import requests
import xml.etree.ElementTree as ET

def inspect_ofac_xml():
    """Download and inspect OFAC SDN XML structure"""
    url = "https://www.treasury.gov/ofac/downloads/sdn.xml"
    
    print(f"Downloading from: {url}")
    response = requests.get(url, timeout=60)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.content)} bytes")
    
    try:
        root = ET.fromstring(response.content)
        
        print(f"\nRoot tag: {root.tag}")
        print(f"Root attributes: {root.attrib}")
        
        # Print first few children
        print("\nFirst level children:")
        for i, child in enumerate(root):
            print(f"  {i+1}. {child.tag} - {len(child)} children")
            if i >= 5:
                break
        
        # Find all unique tags in first 100 elements
        print("\nSearching for entry tags...")
        tags = set()
        for i, elem in enumerate(root.iter()):
            tags.add(elem.tag)
            if i >= 100:
                break
        
        print("\nUnique tags found:")
        for tag in sorted(tags):
            print(f"  - {tag}")
        
        # Try to find SDN entries
        print("\n\nTrying to find SDN entries...")
        sdn_entries = root.findall(".//sdnEntry")
        print(f"Found {len(sdn_entries)} entries with './/sdnEntry'")
        
        # Try other variations
        for path in [".//SDNEntry", ".//entry", ".//Entry", ".//*[local-name()='sdnEntry']"]:
            entries = root.findall(path)
            if entries:
                print(f"Found {len(entries)} entries with '{path}'")
        
        # If entries found, print structure of first entry
        if sdn_entries:
            print("\n\nFirst entry structure:")
            first_entry = sdn_entries[0]
            print(f"Entry tag: {first_entry.tag}")
            print("Entry children:")
            for child in first_entry:
                text = child.text[:50] if child.text else "None"
                print(f"  - {child.tag}: {text}")
        
        # Save sample for inspection
        print("\n\nSaving first 1000 lines to debug_sample.xml...")
        with open("debug_sample.xml", "wb") as f:
            f.write(response.content[:50000])
        print("Sample saved!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    inspect_ofac_xml()
