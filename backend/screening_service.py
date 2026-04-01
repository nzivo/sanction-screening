from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from rapidfuzz import fuzz, process
from models import SanctionsList, PEPList, ScreeningResult
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScreeningService:
    """Service for screening names against sanctions and PEP lists"""
    
    def __init__(self, db: Session, threshold: int = 80):
        self.db = db
        self.threshold = threshold
        self.algorithm = "RapidFuzz"
    
    def _is_valid_country(self, country: Optional[str]) -> bool:
        """Check if country value is valid (not a placeholder)"""
        if not country:
            return False
        # Filter out placeholder/example values
        invalid_values = ['string', 'str', 'example', 'test', 'none', 'null']
        return country.lower().strip() not in invalid_values
    
    def _is_valid_entity_type(self, entity_type: Optional[str]) -> bool:
        """Check if entity_type value is valid (not a placeholder)"""
        if not entity_type:
            return False
        # Filter out placeholder/example values
        invalid_values = ['string', 'str', 'example', 'test', 'none', 'null']
        return entity_type.lower().strip() not in invalid_values
    
    def screen_name(
        self,
        name: str,
        entity_type: Optional[str] = None,
        country: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        client_reference: Optional[str] = None,
        include_pep: bool = True,
        include_sanctions: bool = True
    ) -> Dict:
        """
        Screen a name against sanctions and PEP lists
        
        Args:
            name: Name to screen
            entity_type: Type of entity (Individual, Entity, Vessel)
            country: Country for additional filtering
            date_of_birth: DOB for additional matching
            client_reference: External reference ID
            include_pep: Whether to check PEP lists
            include_sanctions: Whether to check sanctions lists
        
        Returns:
            Dict containing all matches above threshold
        """
        logger.info(f"Screening name: {name}")
        
        results = {
            "query_name": name,
            "query_type": entity_type if self._is_valid_entity_type(entity_type) else "All Types",
            "sanctions_matches": [],
            "pep_matches": [],
            "near_misses": [],  # Matches close to threshold
            "total_matches": 0,
            "highest_score": 0,
            "screening_date": datetime.utcnow().isoformat(),
            "threshold_used": self.threshold,
            "total_records_checked": 0
        }
        
        # Screen against sanctions lists
        if include_sanctions:
            sanctions_result = self._screen_against_sanctions(
                name, entity_type, country, date_of_birth
            )
            results["sanctions_matches"] = sanctions_result["matches"]
            results["near_misses"].extend(sanctions_result["near_misses"])
            results["total_records_checked"] += sanctions_result["total_checked"]
            
            # Save matches to database
            for match in results["sanctions_matches"]:
                self._save_screening_result(
                    query_name=name,
                    query_type=entity_type,
                    matched_list_type="sanctions",
                    match_data=match,
                    client_reference=client_reference,
                    dob=date_of_birth
                )
        
        # Screen against PEP lists
        if include_pep:
            pep_result = self._screen_against_pep(name, country, date_of_birth)
            results["pep_matches"] = pep_result["matches"]
            results["near_misses"].extend(pep_result["near_misses"])
            results["total_records_checked"] += pep_result["total_checked"]
            
            # Save matches to database
            for match in results["pep_matches"]:
                self._save_screening_result(
                    query_name=name,
                    query_type=entity_type,
                    matched_list_type="pep",
                    match_data=match,
                    client_reference=client_reference,
                    dob=date_of_birth
                )
        
        # Calculate totals
        results["total_matches"] = len(results["sanctions_matches"]) + len(results["pep_matches"])
        
        all_scores = [m["match_score"] for m in results["sanctions_matches"]] + \
                     [m["match_score"] for m in results["pep_matches"]]
        results["highest_score"] = max(all_scores) if all_scores else 0
        
        return results
    
    def _screen_against_sanctions(
        self,
        name: str,
        entity_type: Optional[str],
        country: Optional[str],
        date_of_birth: Optional[str]
    ) -> Dict:
        """Screen against sanctions lists"""
        matches = []
        near_misses = []  # Scores between (threshold - 10) and threshold
        
        # Get all active sanctions entries
        query = self.db.query(SanctionsList).filter(SanctionsList.is_active == True)
        
        # Only filter by entity_type if it's a valid value
        if self._is_valid_entity_type(entity_type):
            logger.info(f"Filtering sanctions by entity_type: {entity_type}")
            # Case-insensitive comparison
            query = query.filter(SanctionsList.entity_type.ilike(entity_type))
        else:
            if entity_type:
                logger.info(f"Ignoring invalid entity_type value: '{entity_type}' - searching all types")
            else:
                logger.info("No entity_type specified - searching all types")
        
        # Only filter by country if it's a valid country value
        if self._is_valid_country(country):
            logger.info(f"Filtering sanctions by country: {country}")
            query = query.filter(SanctionsList.country == country)
        else:
            if country:
                logger.info(f"Ignoring invalid country value for sanctions: '{country}'")
        
        sanctions_entries = query.all()
        
        logger.info(f"Screening against {len(sanctions_entries)} sanctions entries")
        
        name_lower = name.lower().strip()
        
        for entry in sanctions_entries:
            # Calculate match score for full name
            full_name_score = fuzz.token_sort_ratio(name_lower, entry.full_name.lower())
            
            # Check aliases
            alias_scores = []
            if entry.aliases:
                for alias in entry.aliases:
                    alias_name = alias.get("name", "")
                    if alias_name:
                        alias_score = fuzz.token_sort_ratio(name_lower, alias_name.lower())
                        alias_scores.append((alias_score, alias_name))
            
            # Get best score
            best_score = full_name_score
            best_match_name = entry.full_name
            match_type = "Fuzzy"
            
            if alias_scores:
                best_alias_score, best_alias_name = max(alias_scores, key=lambda x: x[0])
                if best_alias_score > best_score:
                    best_score = best_alias_score
                    best_match_name = best_alias_name
                    match_type = "Alias"
            
            dob_match = False
            if date_of_birth and entry.date_of_birth:
                dob_match = self._compare_dates(date_of_birth, entry.date_of_birth)
            
            country_match = False
            if self._is_valid_country(country) and entry.country:
                country_match = country.lower() == entry.country.lower()
            
            match_data = {
                "match_id": entry.id,
                "match_score": best_score,
                "match_type": match_type if best_score < 100 else "Exact",
                "matched_name": best_match_name,
                "full_name": entry.full_name,
                "source": entry.source,
                "list_type": entry.list_type,
                "entity_type": entry.entity_type,
                "entity_number": entry.entity_number,
                "country": entry.country,
                "date_of_birth": entry.date_of_birth,
                "programs": entry.programs,
                "remarks": entry.remarks,
                "aliases": entry.aliases[:3] if entry.aliases else [],  # Limit aliases in response
                "dob_match": dob_match,
                "country_match": country_match,
            }
            
            # Check if score meets threshold
            if best_score >= self.threshold:
                matches.append(match_data)
            # Track near misses (within 10 points of threshold)
            elif best_score >= (self.threshold - 10):
                near_misses.append(match_data)
        
        # Sort by match score descending
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        near_misses.sort(key=lambda x: x["match_score"], reverse=True)
        
        logger.info(f"Found {len(matches)} sanctions matches (threshold: {self.threshold}%)")
        if near_misses:
            logger.info(f"Found {len(near_misses)} near misses (score {self.threshold-10}-{self.threshold-1}%)")
        
        return {
            "matches": matches,
            "near_misses": near_misses[:5],  # Return top 5 near misses
            "total_checked": len(sanctions_entries)
        }
    
    def _screen_against_pep(
        self,
        name: str,
        country: Optional[str],
        date_of_birth: Optional[str]
    ) -> Dict:
        """Screen against PEP lists"""
        matches = []
        near_misses = []  # Scores between (threshold - 10) and threshold
        
        # Get all active PEP entries
        query = self.db.query(PEPList).filter(PEPList.is_active == True)
        
        # Only filter by country if it's a valid country value
        if self._is_valid_country(country):
            logger.info(f"Filtering PEPs by country: {country}")
            query = query.filter(PEPList.country == country)
        else:
            if country:
                logger.info(f"Ignoring invalid country value: '{country}'")
        
        pep_entries = query.all()
        
        logger.info(f"Screening against {len(pep_entries)} PEP entries")
        
        name_lower = name.lower().strip()
        
        for entry in pep_entries:
            # Calculate match score
            full_name_score = fuzz.token_sort_ratio(name_lower, entry.full_name.lower())
            
            # Check aliases
            alias_scores = []
            if entry.aliases:
                for alias in entry.aliases:
                    alias_name = alias.get("name", "")
                    if alias_name:
                        alias_score = fuzz.token_sort_ratio(name_lower, alias_name.lower())
                        alias_scores.append((alias_score, alias_name))
            
            # Get best score
            best_score = full_name_score
            best_match_name = entry.full_name
            match_type = "Fuzzy"
            
            if alias_scores:
                best_alias_score, best_alias_name = max(alias_scores, key=lambda x: x[0])
                if best_alias_score > best_score:
                    best_score = best_alias_score
                    best_match_name = best_alias_name
                    match_type = "Alias"
            
            dob_match = False
            if date_of_birth and entry.date_of_birth:
                dob_match = self._compare_dates(date_of_birth, entry.date_of_birth)
            
            country_match = False
            if self._is_valid_country(country) and entry.country:
                country_match = country.lower() == entry.country.lower()
            
            match_data = {
                "match_id": entry.id,
                "match_score": best_score,
                "match_type": match_type if best_score < 100 else "Exact",
                "matched_name": best_match_name,
                "full_name": entry.full_name,
                "source": f"PEP_{entry.country}",
                "country": entry.country,
                "position": entry.position[:200] if entry.position else None,  # Truncate for response
                "position_level": entry.position_level,
                "organization": entry.organization,
                "pep_type": entry.pep_type,
                "status": entry.status,
                "risk_level": entry.risk_level,
                "date_of_birth": entry.date_of_birth,
                "dob_match": dob_match,
                "country_match": country_match,
            }
            
            # Check if score meets threshold
            if best_score >= self.threshold:
                matches.append(match_data)
            # Track near misses (within 10 points of threshold)
            elif best_score >= (self.threshold - 10):
                near_misses.append(match_data)
        
        # Sort by match score descending
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        near_misses.sort(key=lambda x: x["match_score"], reverse=True)
        
        logger.info(f"Found {len(matches)} PEP matches (threshold: {self.threshold}%)")
        if near_misses:
            logger.info(f"Found {len(near_misses)} near misses (score {self.threshold-10}-{self.threshold-1}%)")
        
        return {
            "matches": matches,
            "near_misses": near_misses[:5],  # Return top 5 near misses
            "total_checked": len(pep_entries)
        }
    
    def _compare_dates(self, date1: str, date2: str) -> bool:
        """Compare two dates (handles partial dates)"""
        # Simple comparison - can be enhanced for partial dates
        return date1.strip() == date2.strip()
    
    def _save_screening_result(
        self,
        query_name: str,
        query_type: Optional[str],
        matched_list_type: str,
        match_data: Dict,
        client_reference: Optional[str],
        dob: Optional[str]
    ):
        """Save screening result to database"""
        try:
            result = ScreeningResult(
                query_name=query_name,
                query_type=query_type,
                matched_list_id=match_data["match_id"],
                matched_list_type=matched_list_type,
                matched_source=match_data["source"],
                matched_name=match_data["matched_name"],
                match_score=match_data["match_score"],
                match_type=match_data["match_type"],
                matching_algorithm=self.algorithm,
                name_match_score=match_data["match_score"],
                dob_match=match_data.get("dob_match", False),
                country_match=match_data.get("country_match", False),
                client_reference=client_reference,
                status="Pending"
            )
            
            self.db.add(result)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error saving screening result: {str(e)}")
            self.db.rollback()
    
    def batch_screen(self, names: List[str], **kwargs) -> List[Dict]:
        """Screen multiple names at once"""
        results = []
        
        for name in names:
            try:
                result = self.screen_name(name, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error screening {name}: {str(e)}")
                results.append({
                    "query_name": name,
                    "error": str(e),
                    "total_matches": 0
                })
        
        return results
    
    def get_screening_history(
        self,
        query_name: Optional[str] = None,
        client_reference: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Retrieve screening history"""
        query = self.db.query(ScreeningResult)
        
        if query_name:
            query = query.filter(ScreeningResult.query_name.ilike(f"%{query_name}%"))
        
        if client_reference:
            query = query.filter(ScreeningResult.client_reference == client_reference)
        
        if min_score:
            query = query.filter(ScreeningResult.match_score >= min_score)
        
        results = query.order_by(ScreeningResult.screened_date.desc()).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "query_name": r.query_name,
                "matched_name": r.matched_name,
                "match_score": r.match_score,
                "matched_source": r.matched_source,
                "matched_list_type": r.matched_list_type,
                "status": r.status,
                "screened_date": r.screened_date.isoformat() if r.screened_date else None,
                "client_reference": r.client_reference,
            }
            for r in results
        ]
