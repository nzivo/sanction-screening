"""
Alternative OFAC downloader using CSV format (more reliable)
"""

import requests
import csv
from io import StringIO
from typing import List, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from models import SanctionsList, ListUpdateLog
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OFACCSVDownloader:
    """Download and parse OFAC sanctions lists using CSV format"""
    
    def __init__(self, db: Session):
        self.db = db
        self.source = "OFAC"
    
    def download_sdn_list(self) -> List[Dict]:
        """Download OFAC SDN list in pipe-delimited format"""
        # OFAC provides pipe-delimited files which are easier to parse
        url = "https://www.treasury.gov/ofac/downloads/sdn.csv"
        
        try:
            logger.info(f"Downloading OFAC SDN CSV from {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            return self._parse_sdn_csv(response.text)
        except Exception as e:
            logger.error(f"Error downloading OFAC SDN CSV: {str(e)}")
            # Try pipe-delimited format as fallback
            return self._try_pipe_delimited_format()
    
    def _try_pipe_delimited_format(self) -> List[Dict]:
        """Try the pipe-delimited text format"""
        url = "https://www.treasury.gov/ofac/downloads/sdn.txt"
        
        try:
            logger.info(f"Trying pipe-delimited format from {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            entities = []
            lines = response.text.split('\n')
            
            for line in lines:
                if not line.strip():
                    continue
                
                parts = line.split('|')
                if len(parts) < 4:
                    continue
                
                # SDN format: ent_num|sdn_name|sdn_type|program|title|call_sign|vess_type|tonnage|grt|vess_flag|vess_owner|remarks
                entity = {
                    "source": self.source,
                    "list_type": "SDN",
                    "entity_number": parts[0].strip(),
                    "full_name": parts[1].strip() if len(parts) > 1 else "",
                    "entity_type": parts[2].strip() if len(parts) > 2 else "",
                    "remarks": parts[11].strip() if len(parts) > 11 else "",
                }
                
                # Parse programs
                if len(parts) > 3 and parts[3].strip():
                    entity["programs"] = [parts[3].strip()]
                else:
                    entity["programs"] = []
                
                # Split name into parts if possible
                name = entity["full_name"]
                if name:
                    name_parts = name.split()
                    if len(name_parts) >= 2:
                        entity["first_name"] = name_parts[0]
                        entity["last_name"] = name_parts[-1]
                        if len(name_parts) > 2:
                            entity["middle_name"] = " ".join(name_parts[1:-1])
                
                entity["search_text"] = name.lower()
                entity["aliases"] = []
                
                if entity["full_name"]:
                    entities.append(entity)
            
            logger.info(f"Parsed {len(entities)} entries from pipe-delimited format")
            return entities
            
        except Exception as e:
            logger.error(f"Error with pipe-delimited format: {str(e)}")
            return []
    
    def _parse_sdn_csv(self, csv_text: str) -> List[Dict]:
        """Parse OFAC SDN CSV format"""
        entities = []
        
        try:
            # Try standard CSV
            csv_reader = csv.DictReader(StringIO(csv_text))
            
            for row in csv_reader:
                entity = {
                    "source": self.source,
                    "list_type": "SDN",
                    "entity_number": row.get("ent_num", "").strip(),
                    "full_name": row.get("sdn_name", row.get("name", "")).strip(),
                    "entity_type": row.get("sdn_type", row.get("type", "")).strip(),
                    "remarks": row.get("remarks", "").strip(),
                }
                
                # Parse programs
                program = row.get("program", "").strip()
                entity["programs"] = [program] if program else []
                
                # Split name
                name = entity["full_name"]
                if name:
                    name_parts = name.split()
                    if len(name_parts) >= 2:
                        entity["first_name"] = name_parts[0]
                        entity["last_name"] = name_parts[-1]
                        if len(name_parts) > 2:
                            entity["middle_name"] = " ".join(name_parts[1:-1])
                
                entity["search_text"] = name.lower()
                entity["aliases"] = []
                
                if entity["full_name"]:
                    entities.append(entity)
            
            logger.info(f"Parsed {len(entities)} OFAC SDN entries from CSV")
            return entities
            
        except Exception as e:
            logger.error(f"Error parsing CSV: {str(e)}")
            return []
    
    def save_to_database(self, entities: List[Dict]) -> Dict[str, int]:
        """Save parsed entities to database"""
        log = ListUpdateLog(
            source=self.source,
            list_type="SDN",
            status="In Progress"
        )
        self.db.add(log)
        self.db.commit()
        
        stats = {"added": 0, "updated": 0}
        
        try:
            for entity_data in entities:
                # Check if entity already exists
                existing = self.db.query(SanctionsList).filter(
                    SanctionsList.source == self.source,
                    SanctionsList.entity_number == entity_data.get("entity_number")
                ).first()
                
                if existing and entity_data.get("entity_number"):
                    # Update existing entry
                    for key, value in entity_data.items():
                        setattr(existing, key, value)
                    existing.list_updated_date = datetime.utcnow()
                    stats["updated"] += 1
                else:
                    # Add new entry
                    entity = SanctionsList(**entity_data)
                    entity.list_updated_date = datetime.utcnow()
                    self.db.add(entity)
                    stats["added"] += 1
                
                # Commit in batches of 100
                if (stats["added"] + stats["updated"]) % 100 == 0:
                    self.db.commit()
            
            self.db.commit()
            
            # Update log
            log.status = "Success"
            log.update_completed = datetime.utcnow()
            log.records_added = stats["added"]
            log.records_updated = stats["updated"]
            self.db.commit()
            
            logger.info(f"OFAC SDN list updated: {stats['added']} added, {stats['updated']} updated")
            return stats
            
        except Exception as e:
            log.status = "Failed"
            log.error_message = str(e)
            log.update_completed = datetime.utcnow()
            self.db.commit()
            logger.error(f"Error saving OFAC data: {str(e)}")
            raise
