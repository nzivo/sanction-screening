"""
Quick test script to check PEP database entries
"""
from database import SessionLocal
from models import PEPList

def check_pep_data():
    db = SessionLocal()
    try:
        # Count total PEPs
        total = db.query(PEPList).filter(PEPList.is_active == True).count()
        print(f"\n✓ Total active PEPs in database: {total}\n")
        
        # Check for specific name
        search_name = "SWALEH S ABUBAKAR"
        exact_match = db.query(PEPList).filter(
            PEPList.full_name.ilike(f"%{search_name}%")
        ).first()
        
        if exact_match:
            print(f"✓ Found exact match:")
            print(f"  - ID: {exact_match.id}")
            print(f"  - Name: {exact_match.full_name}")
            print(f"  - Country: {exact_match.country}")
            print(f"  - Position: {exact_match.position[:100]}...")
        else:
            print(f"✗ No exact match found for '{search_name}'")
            print(f"\nSearching for similar names containing 'SWALEH'...")
            similar = db.query(PEPList).filter(
                PEPList.full_name.ilike("%SWALEH%")
            ).all()
            
            if similar:
                for pep in similar:
                    print(f"  - {pep.full_name} ({pep.country})")
            else:
                print("  No similar names found")
        
        # Show sample of all PEPs
        print(f"\nFirst 10 PEPs in database:")
        sample = db.query(PEPList).limit(10).all()
        for pep in sample:
            print(f"  - {pep.full_name} ({pep.country})")
        
        # Test fuzzy matching
        from rapidfuzz import fuzz
        print(f"\n\nTesting fuzzy match scores for '{search_name}':")
        all_peps = db.query(PEPList).filter(PEPList.is_active == True).all()
        
        scores = []
        for pep in all_peps:
            score = fuzz.token_sort_ratio(search_name.lower(), pep.full_name.lower())
            if score >= 70:  # Show scores above 70%
                scores.append((score, pep.full_name, pep.country))
        
        scores.sort(reverse=True)
        
        if scores:
            print("Top matches (score >= 70%):")
            for score, name, country in scores[:10]:
                print(f"  {score}% - {name} ({country})")
        else:
            print("No matches found with score >= 70%")
            print("\nTop 5 closest matches:")
            all_scores = [(fuzz.token_sort_ratio(search_name.lower(), pep.full_name.lower()), 
                          pep.full_name, pep.country) for pep in all_peps]
            all_scores.sort(reverse=True)
            for score, name, country in all_scores[:5]:
                print(f"  {score}% - {name} ({country})")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_pep_data()
