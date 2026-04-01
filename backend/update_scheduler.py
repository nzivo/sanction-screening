"""
Smart update scheduler for sanctions lists.
Checks if updates are needed based on:
1. Time since last successful update
2. Recommended update frequency for each source
3. Remote file modification dates (when available)
"""
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import ListUpdateLog
import logging

logger = logging.getLogger(__name__)


class UpdateScheduler:
    """Manages intelligent update scheduling for sanctions lists"""
    
    # Recommended update intervals for each source (in hours)
    UPDATE_INTERVALS = {
        "OFAC": 24,        # Daily - highly dynamic
        "UN": 168,         # Weekly - changes less frequently
        "EU": 168,         # Weekly - changes moderately
        "UK": 168,         # Weekly - changes moderately
        "FRC_Kenya": 168,  # Weekly - domestic list, changes less frequently
    }
    
    # Minimum time between updates (prevents excessive updates)
    MIN_UPDATE_INTERVAL = 6  # 6 hours minimum
    
    def __init__(self, db: Session):
        self.db = db
    
    def should_update(self, source: str, force: bool = False) -> Dict[str, any]:
        """
        Determine if a list should be updated
        
        Args:
            source: List source (OFAC, UN, EU, UK)
            force: Force update regardless of schedule
            
        Returns:
            Dict with 'should_update', 'reason', and 'last_update' info
        """
        if force:
            return {
                "should_update": True,
                "reason": "Forced update requested",
                "last_update": None
            }
        
        # Get last successful update
        last_update = self.db.query(ListUpdateLog).filter(
            ListUpdateLog.source == source,
            ListUpdateLog.status == "Success"
        ).order_by(desc(ListUpdateLog.update_completed)).first()
        
        # If never updated, update now
        if not last_update or not last_update.update_completed:
            return {
                "should_update": True,
                "reason": "Never updated before",
                "last_update": None
            }
        
        # Check time since last update
        hours_since_update = (datetime.utcnow() - last_update.update_completed).total_seconds() / 3600
        recommended_interval = self.UPDATE_INTERVALS.get(source, 168)  # Default to weekly
        
        # Don't update if within minimum interval
        if hours_since_update < self.MIN_UPDATE_INTERVAL:
            return {
                "should_update": False,
                "reason": f"Updated {hours_since_update:.1f} hours ago (min {self.MIN_UPDATE_INTERVAL}h)",
                "last_update": last_update.update_completed,
                "hours_since_update": hours_since_update
            }
        
        # Check if recommended interval has passed
        if hours_since_update >= recommended_interval:
            return {
                "should_update": True,
                "reason": f"Scheduled update due ({hours_since_update:.1f}h since last, interval: {recommended_interval}h)",
                "last_update": last_update.update_completed,
                "hours_since_update": hours_since_update
            }
        
        # Check if remote file has been modified (if supported)
        remote_modified = self._check_remote_modification(source, last_update.update_completed)
        if remote_modified:
            return {
                "should_update": True,
                "reason": "Remote list has been modified",
                "last_update": last_update.update_completed,
                "hours_since_update": hours_since_update
            }
        
        # Not time to update yet
        hours_until_due = recommended_interval - hours_since_update
        return {
            "should_update": False,
            "reason": f"Update not due yet ({hours_until_due:.1f}h remaining)",
            "last_update": last_update.update_completed,
            "hours_since_update": hours_since_update,
            "hours_until_due": hours_until_due
        }
    
    def _check_remote_modification(self, source: str, last_update: datetime) -> bool:
        """
        Check if remote file has been modified since last update
        Uses HTTP HEAD request to check Last-Modified header
        
        Returns:
            True if modified, False if not or if check failed
        """
        urls = {
            "OFAC": "https://www.treasury.gov/ofac/downloads/sdn.xml",
            "UN": "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
            "UK": "https://ofsistorage.blob.core.windows.net/publishlive/2022format/ConList.csv",
            # EU URL may require auth, so skip remote check
        }
        
        url = urls.get(source)
        if not url:
            return False
        
        try:
            # Use HEAD request to get headers without downloading
            response = requests.head(url, timeout=10, allow_redirects=True)
            
            # Check Last-Modified header
            last_modified_str = response.headers.get('Last-Modified')
            if last_modified_str:
                # Parse Last-Modified header
                from email.utils import parsedate_to_datetime
                last_modified = parsedate_to_datetime(last_modified_str)
                
                # Make timezone-aware if needed
                if last_modified.tzinfo is None:
                    from datetime import timezone
                    last_modified = last_modified.replace(tzinfo=timezone.utc)
                
                if last_update.tzinfo is None:
                    from datetime import timezone
                    last_update = last_update.replace(tzinfo=timezone.utc)
                
                # Compare dates
                if last_modified > last_update:
                    logger.info(f"{source} remote file modified: {last_modified} > {last_update}")
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Could not check remote modification for {source}: {str(e)}")
            return False
    
    def get_update_status(self) -> Dict[str, Dict]:
        """
        Get update status for all sources
        
        Returns:
            Dict mapping source names to their update status
        """
        sources = ["OFAC", "UN", "EU", "UK", "FRC_Kenya"]
        status = {}
        
        for source in sources:
            status[source] = self.should_update(source)
        
        return status
    
    def get_last_update_info(self, source: str) -> Optional[Dict]:
        """Get information about the last update for a source"""
        last_update = self.db.query(ListUpdateLog).filter(
            ListUpdateLog.source == source
        ).order_by(desc(ListUpdateLog.update_started)).first()
        
        if not last_update:
            return None
        
        return {
            "source": last_update.source,
            "list_type": last_update.list_type,
            "status": last_update.status,
            "started": last_update.update_started,
            "completed": last_update.update_completed,
            "records_added": last_update.records_added,
            "records_updated": last_update.records_updated,
            "error_message": last_update.error_message
        }
