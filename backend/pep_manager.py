from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models import PEPList
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PEPManager:
    """Manage Politically Exposed Persons lists"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_pep(
        self,
        country: str,
        full_name: str,
        position: str,
        update_if_exists: bool = True,
        **kwargs
    ) -> tuple[PEPList, bool]:
        """
        Add a new PEP to the database or update if exists
        
        Returns:
            tuple: (PEP object, is_new) where is_new is True if newly created, False if updated
        """
        try:
            # Check if PEP already exists
            existing = self.db.query(PEPList).filter(
                PEPList.country == country,
                PEPList.full_name == full_name,
                PEPList.is_active == True
            ).first()
            
            if existing:
                if update_if_exists:
                    # Update existing PEP
                    existing.position = position
                    existing.position_level = kwargs.get("position_level") or existing.position_level
                    existing.organization = kwargs.get("organization") or existing.organization
                    existing.pep_type = kwargs.get("pep_type", existing.pep_type)
                    existing.status = kwargs.get("status", existing.status)
                    existing.risk_level = kwargs.get("risk_level", existing.risk_level)
                    existing.source = kwargs.get("source", existing.source)
                    
                    if kwargs.get("related_pep"):
                        existing.related_pep = kwargs.get("related_pep")
                    if kwargs.get("date_of_birth"):
                        existing.date_of_birth = kwargs.get("date_of_birth")
                    if kwargs.get("place_of_birth"):
                        existing.place_of_birth = kwargs.get("place_of_birth")
                    if kwargs.get("nationality"):
                        existing.nationality = kwargs.get("nationality")
                    if kwargs.get("start_date"):
                        existing.start_date = kwargs.get("start_date")
                    if kwargs.get("end_date"):
                        existing.end_date = kwargs.get("end_date")
                    if kwargs.get("source_url"):
                        existing.source_url = kwargs.get("source_url")
                    if kwargs.get("notes"):
                        existing.notes = kwargs.get("notes")
                    if kwargs.get("aliases"):
                        existing.aliases = kwargs.get("aliases")
                    
                    self.db.commit()
                    self.db.refresh(existing)
                    logger.info(f"Updated PEP: {full_name} ({country})")
                    return existing, False
                else:
                    logger.info(f"PEP already exists, skipping: {full_name} ({country})")
                    return existing, False
            
            # Parse name into components
            name_parts = full_name.split()
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[-1] if len(name_parts) > 1 else ""
            middle_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else ""
            
            # Create new PEP
            pep = PEPList(
                country=country,
                full_name=full_name,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                position=position,
                position_level=kwargs.get("position_level"),
                organization=kwargs.get("organization"),
                pep_type=kwargs.get("pep_type", "Direct"),
                related_pep=kwargs.get("related_pep"),
                date_of_birth=kwargs.get("date_of_birth"),
                place_of_birth=kwargs.get("place_of_birth"),
                nationality=kwargs.get("nationality", country),
                status=kwargs.get("status", "Active"),
                start_date=kwargs.get("start_date"),
                end_date=kwargs.get("end_date"),
                source=kwargs.get("source", "Manual Entry"),
                source_url=kwargs.get("source_url"),
                risk_level=kwargs.get("risk_level", "Medium"),
                notes=kwargs.get("notes"),
                aliases=kwargs.get("aliases", [])
            )
            
            self.db.add(pep)
            self.db.commit()
            self.db.refresh(pep)
            
            logger.info(f"Added PEP: {full_name} ({country})")
            return pep, True
            
        except Exception as e:
            logger.error(f"Error adding PEP: {str(e)}")
            self.db.rollback()
            raise
    
    def bulk_add_peps(self, pep_data_list: List[Dict], update_if_exists: bool = True) -> Dict[str, int]:
        """
        Add multiple PEPs at once
        
        Args:
            pep_data_list: List of PEP data dictionaries
            update_if_exists: If True, updates existing PEPs; if False, skips them
        
        Returns:
            Dict with counts of added, updated, and failed operations
        """
        stats = {"added": 0, "updated": 0, "failed": 0}
        
        for pep_data in pep_data_list:
            try:
                pep, is_new = self.add_pep(update_if_exists=update_if_exists, **pep_data)
                if is_new:
                    stats["added"] += 1
                else:
                    stats["updated"] += 1
            except Exception as e:
                logger.error(f"Failed to add PEP {pep_data.get('full_name')}: {str(e)}")
                stats["failed"] += 1
        
        logger.info(f"Bulk PEP import: {stats['added']} added, {stats['updated']} updated, {stats['failed']} failed")
        return stats
        return stats
    
    def update_pep(self, pep_id: int, **kwargs) -> Optional[PEPList]:
        """Update an existing PEP"""
        try:
            pep = self.db.query(PEPList).filter(PEPList.id == pep_id).first()
            
            if not pep:
                logger.warning(f"PEP {pep_id} not found")
                return None
            
            for key, value in kwargs.items():
                if hasattr(pep, key) and value is not None:
                    setattr(pep, key, value)
            
            self.db.commit()
            self.db.refresh(pep)
            
            logger.info(f"Updated PEP {pep_id}")
            return pep
            
        except Exception as e:
            logger.error(f"Error updating PEP: {str(e)}")
            self.db.rollback()
            raise
    
    def deactivate_pep(self, pep_id: int) -> bool:
        """Deactivate a PEP (soft delete)"""
        try:
            pep = self.db.query(PEPList).filter(PEPList.id == pep_id).first()
            
            if not pep:
                return False
            
            pep.is_active = False
            pep.status = "Former"
            self.db.commit()
            
            logger.info(f"Deactivated PEP {pep_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating PEP: {str(e)}")
            self.db.rollback()
            raise
    
    def get_pep_by_id(self, pep_id: int) -> Optional[PEPList]:
        """Get a PEP by ID"""
        return self.db.query(PEPList).filter(PEPList.id == pep_id).first()
    
    def search_peps(
        self,
        country: Optional[str] = None,
        name: Optional[str] = None,
        position: Optional[str] = None,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        is_active: bool = True
    ) -> List[PEPList]:
        """Search PEPs with filters"""
        query = self.db.query(PEPList)
        
        if is_active is not None:
            query = query.filter(PEPList.is_active == is_active)
        
        if country:
            query = query.filter(PEPList.country == country)
        
        if name:
            query = query.filter(PEPList.full_name.ilike(f"%{name}%"))
        
        if position:
            query = query.filter(PEPList.position.ilike(f"%{position}%"))
        
        if status:
            query = query.filter(PEPList.status == status)
        
        if risk_level:
            query = query.filter(PEPList.risk_level == risk_level)
        
        return query.all()
    
    def get_peps_by_country(self, country: str, is_active: bool = True) -> List[PEPList]:
        """Get all PEPs for a specific country"""
        return self.db.query(PEPList).filter(
            PEPList.country == country,
            PEPList.is_active == is_active
        ).all()


# Kenya PEP Data - Sample list to get started
KENYA_PEPS = [
    {
        "country": "Kenya",
        "full_name": "William Samoei Ruto",
        "position": "President of the Republic of Kenya",
        "position_level": "National",
        "organization": "Office of the President",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "High",
        "source": "Government of Kenya",
    },
    {
        "country": "Kenya",
        "full_name": "Rigathi Gachagua",
        "position": "Deputy President",
        "position_level": "National",
        "organization": "Office of the Deputy President",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "High",
        "source": "Government of Kenya",
    },
    {
        "country": "Kenya",
        "full_name": "Musalia Mudavadi",
        "position": "Prime Cabinet Secretary",
        "position_level": "National",
        "organization": "Office of the Prime Cabinet Secretary",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "High",
        "source": "Government of Kenya",
    },
    {
        "country": "Kenya",
        "full_name": "Kithure Kindiki",
        "position": "Cabinet Secretary for Interior and National Administration",
        "position_level": "National",
        "organization": "Ministry of Interior",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "High",
        "source": "Government of Kenya",
    },
    {
        "country": "Kenya",
        "full_name": "Alfred Mutua",
        "position": "Cabinet Secretary for Foreign and Diaspora Affairs",
        "position_level": "National",
        "organization": "Ministry of Foreign Affairs",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "High",
        "source": "Government of Kenya",
    },
    {
        "country": "Kenya",
        "full_name": "Njuguna Ndung'u",
        "position": "Cabinet Secretary for National Treasury and Economic Planning",
        "position_level": "National",
        "organization": "National Treasury",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "High",
        "source": "Government of Kenya",
    },
    {
        "country": "Kenya",
        "full_name": "Aden Duale",
        "position": "Cabinet Secretary for Defence",
        "position_level": "National",
        "organization": "Ministry of Defence",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "High",
        "source": "Government of Kenya",
    },
    {
        "country": "Kenya",
        "full_name": "Ezekiel Machogu",
        "position": "Cabinet Secretary for Education",
        "position_level": "National",
        "organization": "Ministry of Education",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "Medium",
        "source": "Government of Kenya",
    },
    {
        "country": "Kenya",
        "full_name": "Susan Nakhumicha",
        "position": "Cabinet Secretary for Health",
        "position_level": "National",
        "organization": "Ministry of Health",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "Medium",
        "source": "Government of Kenya",
    },
    {
        "country": "Kenya",
        "full_name": "Moses Kuria",
        "position": "Cabinet Secretary for Public Service",
        "position_level": "National",
        "organization": "Ministry of Public Service",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "Medium",
        "source": "Government of Kenya",
    },
    # Governors (sample)
    {
        "country": "Kenya",
        "full_name": "Johnson Sakaja",
        "position": "Governor of Nairobi County",
        "position_level": "Regional",
        "organization": "Nairobi County Government",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "High",
        "source": "Nairobi County",
    },
    {
        "country": "Kenya",
        "full_name": "Ferdinand Waititu",
        "position": "Former Governor of Kiambu County",
        "position_level": "Regional",
        "organization": "Kiambu County Government",
        "pep_type": "Direct",
        "status": "Former",
        "risk_level": "High",
        "source": "Kiambu County",
    },
    {
        "country": "Kenya",
        "full_name": "Anne Waiguru",
        "position": "Governor of Kirinyaga County",
        "position_level": "Regional",
        "organization": "Kirinyaga County Government",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "High",
        "source": "Kirinyaga County",
    },
    # Judiciary
    {
        "country": "Kenya",
        "full_name": "Martha Koome",
        "position": "Chief Justice of Kenya",
        "position_level": "National",
        "organization": "Judiciary",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "High",
        "source": "Judiciary of Kenya",
    },
    # Parliament (sample)
    {
        "country": "Kenya",
        "full_name": "Moses Wetangula",
        "position": "Speaker of the National Assembly",
        "position_level": "National",
        "organization": "National Assembly",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "High",
        "source": "Parliament of Kenya",
    },
    {
        "country": "Kenya",
        "full_name": "Amason Kingi",
        "position": "Speaker of the Senate",
        "position_level": "National",
        "organization": "Senate",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "High",
        "source": "Parliament of Kenya",
    },
]


def initialize_kenya_peps(db: Session) -> Dict[str, int]:
    """Initialize Kenya PEP list in database"""
    manager = PEPManager(db)
    return manager.bulk_add_peps(KENYA_PEPS)
