"""
Manager for World Bank Debarred Firms and Individuals
Handles upload, search, and management of World Bank sanctions list
"""
from sqlalchemy.orm import Session
from models import SanctionsList, ListUpdateLog
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WorldBankManager:
    """Manage World Bank Debarred Entities"""
    
    def __init__(self, db: Session):
        self.db = db
        self.source = "WorldBank"
        self.list_type = "Debarred"
    
    def bulk_add_entities(self, entities_data: List[Dict], update_if_exists: bool = True) -> Dict[str, int]:
        """
        Bulk add World Bank debarred entities
        
        Args:
            entities_data: List of entity dictionaries
            update_if_exists: Whether to update existing entries
            
        Returns:
            Dict with stats: added, updated, failed
        """
        stats = {"added": 0, "updated": 0, "failed": 0}
        
        # Create update log
        log = ListUpdateLog(
            source=self.source,
            list_type=self.list_type,
            status="In Progress"
        )
        self.db.add(log)
        self.db.commit()
        
        try:
            for entity_data in entities_data:
                try:
                    # Check if entity already exists
                    existing = None
                    if entity_data.get("entity_number"):
                        existing = self.db.query(SanctionsList).filter(
                            SanctionsList.source == self.source,
                            SanctionsList.entity_number == entity_data["entity_number"]
                        ).first()
                    
                    # If not found by entity_number, try by name
                    if not existing:
                        existing = self.db.query(SanctionsList).filter(
                            SanctionsList.source == self.source,
                            SanctionsList.full_name == entity_data["full_name"]
                        ).first()
                    
                    if existing and update_if_exists:
                        # Update existing entity
                        for key, value in entity_data.items():
                            setattr(existing, key, value)
                        existing.updated_date = datetime.utcnow()
                        existing.list_updated_date = datetime.utcnow()
                        stats["updated"] += 1
                    elif not existing:
                        # Add new entity
                        entity = SanctionsList(**entity_data)
                        entity.list_updated_date = datetime.utcnow()
                        entity.source = self.source
                        entity.list_type = self.list_type
                        self.db.add(entity)
                        stats["added"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing entity: {str(e)}")
                    stats["failed"] += 1
            
            self.db.commit()
            
            # Update log with success
            log.status = "Success"
            log.update_completed = datetime.utcnow()
            log.records_added = stats["added"]
            log.records_updated = stats["updated"]
            self.db.commit()
            
            logger.info(f"World Bank entities processed: {stats}")
            return stats
            
        except Exception as e:
            log.status = "Failed"
            log.error_message = str(e)
            log.update_completed = datetime.utcnow()
            self.db.commit()
            logger.error(f"Error in bulk add: {str(e)}")
            raise
    
    def get_entity_by_id(self, entity_id: int) -> Optional[SanctionsList]:
        """Get a World Bank entity by ID"""
        return self.db.query(SanctionsList).filter(
            SanctionsList.id == entity_id,
            SanctionsList.source == self.source
        ).first()
    
    def get_entity_by_name(self, name: str) -> Optional[SanctionsList]:
        """Get a World Bank entity by name"""
        return self.db.query(SanctionsList).filter(
            SanctionsList.source == self.source,
            SanctionsList.full_name == name
        ).first()
    
    def search_entities(
        self, 
        name: Optional[str] = None,
        country: Optional[str] = None,
        is_active: bool = True,
        limit: int = 100
    ) -> List[SanctionsList]:
        """
        Search World Bank debarred entities
        
        Args:
            name: Name to search (partial match)
            country: Country filter
            is_active: Filter by active status
            limit: Maximum results
            
        Returns:
            List of matching entities
        """
        query = self.db.query(SanctionsList).filter(
            SanctionsList.source == self.source,
            SanctionsList.is_active == is_active
        )
        
        if name:
            query = query.filter(
                SanctionsList.full_name.ilike(f"%{name}%")
            )
        
        if country:
            query = query.filter(
                SanctionsList.country.ilike(f"%{country}%")
            )
        
        return query.limit(limit).all()
    
    def get_all_entities(self, is_active: bool = True, limit: int = 1000) -> List[SanctionsList]:
        """Get all World Bank entities"""
        return self.db.query(SanctionsList).filter(
            SanctionsList.source == self.source,
            SanctionsList.is_active == is_active
        ).limit(limit).all()
    
    def get_count(self, is_active: bool = True) -> int:
        """Get count of World Bank entities"""
        return self.db.query(SanctionsList).filter(
            SanctionsList.source == self.source,
            SanctionsList.is_active == is_active
        ).count()
    
    def deactivate_entity(self, entity_id: int) -> bool:
        """Deactivate a World Bank entity"""
        entity = self.get_entity_by_id(entity_id)
        if entity:
            entity.is_active = False
            entity.updated_date = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def delete_entity(self, entity_id: int) -> bool:
        """Delete a World Bank entity"""
        entity = self.get_entity_by_id(entity_id)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False
    
    def clear_all_entities(self) -> int:
        """Clear all World Bank entities (use with caution!)"""
        count = self.db.query(SanctionsList).filter(
            SanctionsList.source == self.source
        ).delete()
        self.db.commit()
        logger.info(f"Cleared {count} World Bank entities")
        return count
