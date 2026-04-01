import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models import SanctionsList, ListUpdateLog
import logging
import pandas as pd
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OFACDownloader:
    """Download and parse OFAC sanctions lists"""
    
    def __init__(self, db: Session):
        self.db = db
        self.source = "OFAC"
    
    def download_sdn_list(self) -> List[Dict]:
        """Download OFAC SDN (Specially Designated Nationals) list"""
        url = "https://www.treasury.gov/ofac/downloads/sdn.xml"
        
        try:
            logger.info(f"Downloading OFAC SDN list from {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            return self._parse_sdn_xml(response.content)
        except Exception as e:
            logger.error(f"Error downloading OFAC SDN list: {str(e)}")
            raise
    
    def _parse_sdn_xml(self, xml_content: bytes) -> List[Dict]:
        """Parse OFAC SDN XML format"""
        entities = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Extract namespace from root tag
            namespace = None
            if '}' in root.tag:
                namespace = root.tag.split('}')[0].strip('{')
                logger.info(f"Detected namespace: {namespace}")
            
            # Define namespace for findall
            ns = {'ns': namespace} if namespace else {}
            
            # Find SDN entries with proper namespace handling
            if namespace:
                sdn_entries = root.findall("ns:sdnEntry", ns)
            else:
                sdn_entries = root.findall("sdnEntry")
            
            logger.info(f"Found {len(sdn_entries)} SDN entries")
            
            # Parse SDN entries
            for entry in sdn_entries:
                # Get all text fields flexibly with namespace
                first_name = self._get_text_ns(entry, "firstName", ns)
                last_name = self._get_text_ns(entry, "lastName", ns)
                
                # Handle case where name might be in different field
                if not first_name and not last_name:
                    first_name = self._get_text_ns(entry, "name", ns)
                
                full_name = f"{first_name} {last_name}".strip()
                if not full_name:
                    # For entities, the name might be just in one field
                    full_name = first_name or last_name
                
                if not full_name:
                    # Skip entries without names
                    continue
                
                entity = {
                    "source": self.source,
                    "list_type": "SDN",
                    "entity_number": self._get_text_ns(entry, "uid", ns),
                    "entity_type": self._get_text_ns(entry, "sdnType", ns) or self._get_text_ns(entry, "type", ns),
                    "full_name": full_name,
                    "first_name": first_name,
                    "last_name": last_name,
                    "remarks": self._get_text_ns(entry, "remarks", ns) or self._get_text_ns(entry, "comment", ns),
                }
                
                # Parse program list
                programs = []
                if namespace:
                    program_list = entry.find("ns:programList", ns)
                    if program_list is not None:
                        for program in program_list.findall("ns:program", ns):
                            if program.text:
                                programs.append(program.text.strip())
                else:
                    for program in entry.findall(".//program"):
                        if program.text:
                            programs.append(program.text.strip())
                entity["programs"] = programs
                
                # Parse aliases/AKAs
                aliases = []
                if namespace:
                    aka_list = entry.find("ns:akaList", ns)
                    if aka_list is not None:
                        for aka in aka_list.findall("ns:aka", ns):
                            aka_type = self._get_text_ns(aka, "type", ns) or self._get_text_ns(aka, "category", ns)
                            first = self._get_text_ns(aka, "firstName", ns)
                            last = self._get_text_ns(aka, "lastName", ns)
                            alias_name = f"{first} {last}".strip()
                            if not alias_name:
                                alias_name = self._get_text_ns(aka, "name", ns)
                            if alias_name:
                                aliases.append({
                                    "type": aka_type,
                                    "name": alias_name
                                })
                else:
                    for aka in entry.findall(".//aka"):
                        aka_type = self._get_text(aka, "type")
                        first = self._get_text(aka, "firstName")
                        last = self._get_text(aka, "lastName")
                        alias_name = f"{first} {last}".strip()
                        if alias_name:
                            aliases.append({
                                "type": aka_type,
                                "name": alias_name
                            })
                entity["aliases"] = aliases
                
                # Parse addresses
                addresses = []
                if namespace:
                    addr_list = entry.find("ns:addressList", ns)
                    if addr_list is not None:
                        for address in addr_list.findall("ns:address", ns):
                            addr = {
                                "address": self._get_text_ns(address, "address1", ns),
                                "city": self._get_text_ns(address, "city", ns),
                                "country": self._get_text_ns(address, "country", ns),
                                "postal_code": self._get_text_ns(address, "postalCode", ns),
                            }
                            addresses.append(addr)
                else:
                    for address in entry.findall(".//address"):
                        addr = {
                            "address": self._get_text(address, "address1"),
                            "city": self._get_text(address, "city"),
                            "country": self._get_text(address, "country"),
                            "postal_code": self._get_text(address, "postalCode"),
                        }
                        addresses.append(addr)
                
                if addresses:
                    entity["address"] = addresses[0].get("address")
                    entity["city"] = addresses[0].get("city")
                    entity["country"] = addresses[0].get("country")
                    entity["postal_code"] = addresses[0].get("postal_code")
                
                # Note: ID fields (passport, national ID, etc.) may not be in all XML formats
                # They can be added if present in idList structure
                
                # Create search text for full-text search
                entity["search_text"] = self._create_search_text(entity)
                
                entities.append(entity)
            
            logger.info(f"Parsed {len(entities)} OFAC SDN entries")
            return entities
            
        except Exception as e:
            logger.error(f"Error parsing OFAC SDN XML: {str(e)}", exc_info=True)
            raise
    
    def _get_text(self, element: ET.Element, tag: str) -> str:
        """Safely extract text from XML element"""
        found = element.find(f".//{tag}")
        return found.text.strip() if found is not None and found.text else ""
    
    def _get_text_ns(self, element: ET.Element, tag: str, ns: Dict) -> str:
        """Safely extract text from XML element with namespace"""
        if ns and 'ns' in ns:
            found = element.find(f"ns:{tag}", ns)
        else:
            found = element.find(tag)
        return found.text.strip() if found is not None and found.text else ""
    
    def _create_search_text(self, entity: Dict) -> str:
        """Create searchable text from entity data (truncated to fit index limits)"""
        parts = [
            entity.get("full_name", ""),
            entity.get("first_name", ""),
            entity.get("last_name", ""),
        ]
        
        # Add aliases
        if entity.get("aliases"):
            for alias in entity["aliases"]:
                parts.append(alias.get("name", ""))
        
        # PostgreSQL btree index limit is ~2704 bytes
        # Truncate to 500 chars (max ~2000 bytes with UTF-8) to be safe
        search_text = " ".join(filter(None, parts)).lower()
        return search_text[:500] if len(search_text) > 500 else search_text
    
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
                
                if existing:
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


class UNDownloader:
    """Download and parse UN Consolidated Sanctions List"""
    
    def __init__(self, db: Session):
        self.db = db
        self.source = "UN"
    
    def download_consolidated_list(self) -> List[Dict]:
        """Download UN Consolidated Sanctions List"""
        url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
        
        try:
            logger.info(f"Downloading UN Consolidated list from {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            return self._parse_un_xml(response.content)
        except Exception as e:
            logger.error(f"Error downloading UN list: {str(e)}")
            raise
    
    def _parse_un_xml(self, xml_content: bytes) -> List[Dict]:
        """Parse UN XML format"""
        entities = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Parse individuals
            for individual in root.findall(".//INDIVIDUAL"):
                entity = self._parse_individual(individual)
                entities.append(entity)
            
            # Parse entities
            for org in root.findall(".//ENTITY"):
                entity = self._parse_entity(org)
                entities.append(entity)
            
            logger.info(f"Parsed {len(entities)} UN entries")
            return entities
            
        except Exception as e:
            logger.error(f"Error parsing UN XML: {str(e)}")
            raise
    
    def _parse_individual(self, element: ET.Element) -> Dict:
        """Parse individual entry"""
        entity = {
            "source": self.source,
            "list_type": "Consolidated",
            "entity_type": "Individual",
            "reference_number": self._get_text(element, "REFERENCE_NUMBER"),
            "entity_number": self._get_text(element, "DATAID"),
        }
        
        # Name
        first_name = self._get_text(element, "FIRST_NAME")
        second_name = self._get_text(element, "SECOND_NAME")
        third_name = self._get_text(element, "THIRD_NAME")
        
        entity["first_name"] = first_name
        entity["middle_name"] = second_name
        entity["last_name"] = third_name
        entity["full_name"] = " ".join(filter(None, [first_name, second_name, third_name]))
        
        # Additional info
        entity["date_of_birth"] = self._get_text(element, "INDIVIDUAL_DATE_OF_BIRTH")
        entity["place_of_birth"] = self._get_text(element, "INDIVIDUAL_PLACE_OF_BIRTH")
        
        # Aliases
        aliases = []
        for alias in element.findall(".//INDIVIDUAL_ALIAS"):
            alias_name = self._get_text(alias, "ALIAS_NAME")
            if alias_name:
                aliases.append({"name": alias_name, "quality": self._get_text(alias, "QUALITY")})
        entity["aliases"] = aliases
        
        # Address
        addresses = []
        for addr in element.findall(".//INDIVIDUAL_ADDRESS"):
            addresses.append({
                "street": self._get_text(addr, "STREET"),
                "city": self._get_text(addr, "CITY"),
                "country": self._get_text(addr, "COUNTRY"),
            })
        
        if addresses:
            entity["address"] = addresses[0].get("street")
            entity["city"] = addresses[0].get("city")
            entity["country"] = addresses[0].get("country")
        
        # Nationality
        for nat in element.findall(".//NATIONALITY"):
            entity["nationality"] = self._get_text(nat, "VALUE")
            break
        
        # Comments
        entity["remarks"] = self._get_text(element, "COMMENTS1")
        
        entity["search_text"] = self._create_search_text(entity)
        
        return entity
    
    def _parse_entity(self, element: ET.Element) -> Dict:
        """Parse entity/organization entry"""
        entity = {
            "source": self.source,
            "list_type": "Consolidated",
            "entity_type": "Entity",
            "reference_number": self._get_text(element, "REFERENCE_NUMBER"),
            "entity_number": self._get_text(element, "DATAID"),
            "full_name": self._get_text(element, "FIRST_NAME"),
        }
        
        # Aliases
        aliases = []
        for alias in element.findall(".//ENTITY_ALIAS"):
            alias_name = self._get_text(alias, "ALIAS_NAME")
            if alias_name:
                aliases.append({"name": alias_name, "quality": self._get_text(alias, "QUALITY")})
        entity["aliases"] = aliases
        
        # Address
        addresses = []
        for addr in element.findall(".//ENTITY_ADDRESS"):
            addresses.append({
                "street": self._get_text(addr, "STREET"),
                "city": self._get_text(addr, "CITY"),
                "country": self._get_text(addr, "COUNTRY"),
            })
        
        if addresses:
            entity["address"] = addresses[0].get("street")
            entity["city"] = addresses[0].get("city")
            entity["country"] = addresses[0].get("country")
        
        entity["remarks"] = self._get_text(element, "COMMENTS1")
        entity["search_text"] = self._create_search_text(entity)
        
        return entity
    
    def _get_text(self, element: ET.Element, tag: str) -> str:
        """Safely extract text from XML element"""
        found = element.find(f".//{tag}")
        return found.text.strip() if found is not None and found.text else ""
    
    def _create_search_text(self, entity: Dict) -> str:
        """Create searchable text from entity data (truncated to fit index limits)"""
        parts = [
            entity.get("full_name", ""),
            entity.get("first_name", ""),
            entity.get("middle_name", ""),
            entity.get("last_name", ""),
        ]
        
        if entity.get("aliases"):
            for alias in entity["aliases"]:
                parts.append(alias.get("name", ""))
        
        # PostgreSQL btree index limit is ~2704 bytes
        # Truncate to 500 chars (max ~2000 bytes with UTF-8) to be safe
        search_text = " ".join(filter(None, parts)).lower()
        return search_text[:500] if len(search_text) > 500 else search_text
    
    def save_to_database(self, entities: List[Dict]) -> Dict[str, int]:
        """Save parsed entities to database"""
        log = ListUpdateLog(
            source=self.source,
            list_type="Consolidated",
            status="In Progress"
        )
        self.db.add(log)
        self.db.commit()
        
        stats = {"added": 0, "updated": 0}
        
        try:
            for entity_data in entities:
                existing = self.db.query(SanctionsList).filter(
                    SanctionsList.source == self.source,
                    SanctionsList.entity_number == entity_data.get("entity_number")
                ).first()
                
                if existing:
                    for key, value in entity_data.items():
                        setattr(existing, key, value)
                    existing.list_updated_date = datetime.utcnow()
                    stats["updated"] += 1
                else:
                    entity = SanctionsList(**entity_data)
                    entity.list_updated_date = datetime.utcnow()
                    self.db.add(entity)
                    stats["added"] += 1
            
            self.db.commit()
            
            log.status = "Success"
            log.update_completed = datetime.utcnow()
            log.records_added = stats["added"]
            log.records_updated = stats["updated"]
            self.db.commit()
            
            logger.info(f"UN list updated: {stats['added']} added, {stats['updated']} updated")
            return stats
            
        except Exception as e:
            log.status = "Failed"
            log.error_message = str(e)
            log.update_completed = datetime.utcnow()
            self.db.commit()
            logger.error(f"Error saving UN data: {str(e)}")
            raise


class EUDownloader:
    """Download and parse EU Financial Sanctions List"""
    
    def __init__(self, db: Session):
        self.db = db
        self.source = "EU"
    
    def download_sanctions_list(self) -> List[Dict]:
        """Download EU Financial Sanctions List"""
        # Working URL with public token
        primary_url = "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList/content?token=dG9rZW4tMjAxNw"
        
        # Alternative: File 1.1 format (newer version)
        alternative_url = "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw"
        
        # Try primary URL first
        try:
            logger.info(f"Downloading EU sanctions list (File 1.0 format)...")
            response = requests.get(primary_url, timeout=60)
            response.raise_for_status()
            logger.info("Successfully downloaded EU sanctions list")
            return self._parse_eu_xml(response.content)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.warning(f"Primary EU URL returned 403 Forbidden - trying File 1.1 format...")
                # Try alternative URL
                try:
                    response = requests.get(alternative_url, timeout=60)
                    response.raise_for_status()
                    logger.info("Successfully downloaded EU sanctions list (File 1.1 format)")
                    return self._parse_eu_xml(response.content)
                except Exception as alt_error:
                    logger.error(f"Alternative EU URL also failed: {str(alt_error)}")
                    raise Exception(
                        f"EU sanctions list download failed with both formats. "
                        f"The public token may have expired. "
                        f"For manual download, visit: https://www.sanctionsmap.eu/ "
                        f"or check https://webgate.ec.europa.eu/fsd/fsf for updated tokens."
                    )
            else:
                logger.error(f"Error downloading EU list: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Error downloading EU list: {str(e)}")
            raise
    
    def _parse_eu_xml(self, xml_content: bytes) -> List[Dict]:
        """Parse EU XML format"""
        entities = []
        
        try:
            root = ET.fromstring(xml_content)
            ns = "{http://eu.europa.ec/fpi/fsd/export}"
            
            # Parse all sanctionEntity elements
            for sanction_entity in root.findall(f".//{ns}sanctionEntity"):
                # Check if person or entity
                subject_type = sanction_entity.find(f".//{ns}subjectType")
                if subject_type is not None:
                    entity_code = subject_type.get("code", "")
                    if entity_code == "person":
                        entity = self._parse_person(sanction_entity)
                    else:  # entity, enterprise, etc.
                        entity = self._parse_organization(sanction_entity)
                    entities.append(entity)
            
            logger.info(f"Parsed {len(entities)} EU entries")
            return entities
            
        except Exception as e:
            logger.error(f"Error parsing EU XML: {str(e)}")
            raise
    
    def _parse_person(self, element: ET.Element) -> Dict:
        """Parse person entry"""
        ns = "{http://eu.europa.ec/fpi/fsd/export}"
        
        entity = {
            "source": self.source,
            "list_type": "EU Sanctions",
            "entity_type": "Individual",
            "entity_number": element.get("logicalId", ""),
            "reference_number": element.get("unitedNationId", ""),
        }
        
        # Name information - get first nameAlias with strong="true"
        name_aliases = element.findall(f".//{ns}nameAlias")
        if name_aliases:
            primary_alias = name_aliases[0]
            entity["full_name"] = primary_alias.get("wholeName", "")
            entity["first_name"] = primary_alias.get("firstName", "")
            entity["last_name"] = primary_alias.get("lastName", "")
            
            # Collect other aliases
            aliases = []
            for alias in name_aliases[1:]:  # Skip first one (primary name)
                alias_name = alias.get("wholeName")
                if alias_name:
                    aliases.append({"name": alias_name, "type": "a.k.a."})
            entity["aliases"] = aliases
        else:
            entity["full_name"] = ""
            entity["aliases"] = []
        
        # Birth information
        birth_date_elem = element.find(f".//{ns}birthdate")
        if birth_date_elem is not None:
            entity["date_of_birth"] = birth_date_elem.get("birthdate", "")
            entity["place_of_birth"] = birth_date_elem.get("city", "")
        
        # Citizenship
        citizenship = element.find(f".//{ns}citizenship")
        if citizenship is not None:
            entity["nationality"] = citizenship.get("countryDescription", "")
        
        # Address
        address_elem = element.find(f".//{ns}address")
        if address_elem is not None:
            entity["address"] = address_elem.get("street", "")
            entity["city"] = address_elem.get("city", "")
            entity["country"] = address_elem.get("countryDescription", "")
            entity["postal_code"] = address_elem.get("zipCode", "")
        
        # Remarks/Comments
        remark = element.find(f".//{ns}remark")
        if remark is not None and remark.text:
            entity["remarks"] = remark.text.strip()
        
        entity["search_text"] = self._create_search_text(entity)
        
        return entity
    
    def _parse_organization(self, element: ET.Element) -> Dict:
        """Parse organization/entity entry"""
        ns = "{http://eu.europa.ec/fpi/fsd/export}"
        
        entity = {
            "source": self.source,
            "list_type": "EU Sanctions",
            "entity_type": "Entity",
            "entity_number": element.get("logicalId", ""),
            "reference_number": element.get("unitedNationId", ""),
        }
        
        # Name - get first nameAlias
        name_aliases = element.findall(f".//{ns}nameAlias")
        if name_aliases:
            primary_alias = name_aliases[0]
            entity["full_name"] = primary_alias.get("wholeName", "")
            
            # Collect other aliases
            aliases = []
            for alias in name_aliases[1:]:  # Skip first one (primary name)
                alias_name = alias.get("wholeName")
                if alias_name:
                    aliases.append({"name": alias_name, "type": "a.k.a."})
            entity["aliases"] = aliases
        else:
            entity["full_name"] = ""
            entity["aliases"] = []
        
        # Address
        address_elem = element.find(f".//{ns}address")
        if address_elem is not None:
            entity["address"] = address_elem.get("street", "")
            entity["city"] = address_elem.get("city", "")
            entity["country"] = address_elem.get("countryDescription", "")
            entity["postal_code"] = address_elem.get("zipCode", "")
        
        # Remarks
        remark = element.find(f".//{ns}remark")
        if remark is not None and remark.text:
            entity["remarks"] = remark.text.strip()
        
        entity["search_text"] = self._create_search_text(entity)
        
        return entity
    
    def _create_search_text(self, entity: Dict) -> str:
        """Create searchable text from entity data (truncated to fit index limits)"""
        parts = [
            entity.get("full_name", ""),
            entity.get("first_name", ""),
            entity.get("last_name", ""),
        ]
        
        if entity.get("aliases"):
            for alias in entity["aliases"]:
                parts.append(alias.get("name", ""))
        
        # PostgreSQL btree index limit is ~2704 bytes
        # Truncate to 500 chars (max ~2000 bytes with UTF-8) to be safe
        search_text = " ".join(filter(None, parts)).lower()
        return search_text[:500] if len(search_text) > 500 else search_text
    
    def save_to_database(self, entities: List[Dict]) -> Dict[str, int]:
        """Save parsed entities to database"""
        log = ListUpdateLog(
            source=self.source,
            list_type="EU Sanctions",
            status="In Progress"
        )
        self.db.add(log)
        self.db.commit()
        
        stats = {"added": 0, "updated": 0}
        
        try:
            for entity_data in entities:
                existing = self.db.query(SanctionsList).filter(
                    SanctionsList.source == self.source,
                    SanctionsList.entity_number == entity_data.get("entity_number")
                ).first()
                
                if existing:
                    for key, value in entity_data.items():
                        setattr(existing, key, value)
                    existing.list_updated_date = datetime.utcnow()
                    stats["updated"] += 1
                else:
                    entity = SanctionsList(**entity_data)
                    entity.list_updated_date = datetime.utcnow()
                    self.db.add(entity)
                    stats["added"] += 1
            
            self.db.commit()
            
            log.status = "Success"
            log.update_completed = datetime.utcnow()
            log.records_added = stats["added"]
            log.records_updated = stats["updated"]
            self.db.commit()
            
            logger.info(f"EU list updated: {stats['added']} added, {stats['updated']} updated")
            return stats
            
        except Exception as e:
            log.status = "Failed"
            log.error_message = str(e)
            log.update_completed = datetime.utcnow()
            self.db.commit()
            logger.error(f"Error saving EU data: {str(e)}")
            raise


class UKDownloader:
    """Download and parse UK HM Treasury Consolidated Sanctions List"""
    
    def __init__(self, db: Session):
        self.db = db
        self.source = "UK"
    
    def download_sanctions_list(self) -> List[Dict]:
        """Download UK Consolidated Sanctions List (CSV format)"""
        # UK provides both CSV and XLSX formats
        url = "https://ofsistorage.blob.core.windows.net/publishlive/2022format/ConList.csv"
        
        try:
            logger.info(f"Downloading UK sanctions list from {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            return self._parse_uk_csv(response.content)
        except Exception as e:
            logger.error(f"Error downloading UK list: {str(e)}")
            raise
    
    def _parse_uk_csv(self, csv_content: bytes) -> List[Dict]:
        """Parse UK CSV format"""
        entities = []
        
        try:
            # Read CSV content
            import csv
            from io import StringIO
            
            csv_text = csv_content.decode('utf-8-sig')  # Handle BOM if present
            csv_reader = csv.DictReader(StringIO(csv_text))
            
            current_entity = None
            for row in csv_reader:
                # UK CSV has one row per entry
                group_type = row.get("Group Type", "").strip()
                
                entity = {
                    "source": self.source,
                    "list_type": "UK Consolidated",
                    "entity_type": "Individual" if group_type == "Individual" else "Entity",
                    "entity_number": row.get("Group ID", ""),
                    "reference_number": row.get("Unique ID", ""),
                }
                
                # Name fields
                if group_type == "Individual":
                    entity["full_name"] = row.get("Name 6", "").strip()
                    entity["first_name"] = row.get("Name 1", "").strip()
                    entity["last_name"] = row.get("Name 2", "").strip()
                else:
                    entity["full_name"] = row.get("Name 6", "").strip()
                
                # Aliases - captured from Name 1-5 fields
                aliases = []
                alias_fields = ["Alias - Name", "Name 1", "Name 2", "Name 3", "Name 4", "Name 5"]
                for field in alias_fields:
                    alias_name = row.get(field, "").strip()
                    if alias_name and alias_name != entity.get("full_name"):
                        aliases.append({"name": alias_name, "type": "a.k.a."})
                entity["aliases"] = aliases
                
                # Date of birth
                dob = row.get("DOB", "").strip()
                if dob:
                    entity["date_of_birth"] = dob
                
                # Place of birth
                pob = row.get("Town of Birth", "").strip() or row.get("Country of Birth", "").strip()
                if pob:
                    entity["place_of_birth"] = pob
                
                # Nationality
                nationality = row.get("Nationality", "").strip()
                if nationality:
                    entity["nationality"] = nationality
                
                # Address
                address_parts = []
                for field in ["Address 1", "Address 2", "Address 3"]:
                    addr_part = row.get(field, "").strip()
                    if addr_part:
                        address_parts.append(addr_part)
                
                if address_parts:
                    entity["address"] = ", ".join(address_parts)
                
                entity["city"] = row.get("Address 4", "").strip() or row.get("Address 5", "").strip()
                entity["country"] = row.get("Address 6", "").strip() or row.get("Country", "").strip()
                entity["postal_code"] = row.get("Post/Zip Code", "").strip()
                
                # Regime/Programs
                regime = row.get("Regime", "").strip()
                if regime:
                    entity["programs"] = [regime]
                else:
                    entity["programs"] = []
                
                # Listed date
                listed_on = row.get("Listed on", "").strip()
                if listed_on:
                    entity["listed_date"] = listed_on
                
                # Remarks/Comments
                entity["remarks"] = row.get("Other Information", "").strip()
                
                entity["search_text"] = self._create_search_text(entity)
                entities.append(entity)
            
            logger.info(f"Parsed {len(entities)} UK entries")
            return entities
            
        except Exception as e:
            logger.error(f"Error parsing UK CSV: {str(e)}")
            raise
    
    def _create_search_text(self, entity: Dict) -> str:
        """Create searchable text from entity data (truncated to fit index limits)"""
        parts = [
            entity.get("full_name", ""),
            entity.get("first_name", ""),
            entity.get("last_name", ""),
        ]
        
        if entity.get("aliases"):
            for alias in entity["aliases"]:
                parts.append(alias.get("name", ""))
        
        # PostgreSQL btree index limit is ~2704 bytes
        # Truncate to 500 chars (max ~2000 bytes with UTF-8) to be safe
        search_text = " ".join(filter(None, parts)).lower()
        return search_text[:500] if len(search_text) > 500 else search_text
    
    def save_to_database(self, entities: List[Dict]) -> Dict[str, int]:
        """Save parsed entities to database"""
        log = ListUpdateLog(
            source=self.source,
            list_type="UK Consolidated",
            status="In Progress"
        )
        self.db.add(log)
        self.db.commit()
        
        stats = {"added": 0, "updated": 0}
        
        try:
            for entity_data in entities:
                existing = self.db.query(SanctionsList).filter(
                    SanctionsList.source == self.source,
                    SanctionsList.entity_number == entity_data.get("entity_number")
                ).first()
                
                if existing:
                    for key, value in entity_data.items():
                        setattr(existing, key, value)
                    existing.list_updated_date = datetime.utcnow()
                    stats["updated"] += 1
                else:
                    entity = SanctionsList(**entity_data)
                    entity.list_updated_date = datetime.utcnow()
                    self.db.add(entity)
                    stats["added"] += 1
            
            self.db.commit()
            
            log.status = "Success"
            log.update_completed = datetime.utcnow()
            log.records_added = stats["added"]
            log.records_updated = stats["updated"]
            self.db.commit()
            
            logger.info(f"UK list updated: {stats['added']} added, {stats['updated']} updated")
            return stats
            
        except Exception as e:
            log.status = "Failed"
            log.error_message = str(e)
            log.update_completed = datetime.utcnow()
            self.db.commit()
            logger.error(f"Error saving UK data: {str(e)}")
            raise


class FRCKenyaDownloader:
    """Download and parse FRC Kenya domestic sanctions list"""
    
    def __init__(self, db: Session):
        self.db = db
        self.source = "FRC_Kenya"
        # Default URL - user can override if URL changes
        self.url = "https://www.frc.go.ke/wp-content/uploads/2026/02/Domestic-List_Kenya.xlsx"
    
    def download_sanctions_list(self, custom_url: Optional[str] = None) -> List[Dict]:
        """Download FRC Kenya domestic list (Excel format)"""
        url = custom_url or self.url
        
        try:
            logger.info(f"Downloading FRC Kenya domestic list from {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            return self._parse_excel(response.content)
        except Exception as e:
            logger.error(f"Error downloading FRC Kenya list: {str(e)}")
            raise
    
    def _parse_excel(self, content: bytes) -> List[Dict]:
        """Parse FRC Kenya Excel format matching official structure"""
        entities = []
        
        try:
            # Read Excel file
            df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
            
            logger.info(f"Found {len(df)} rows in FRC Kenya list")
            logger.info(f"Columns: {df.columns.tolist()}")
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            for idx, row in df.iterrows():
                # Skip empty rows - check Full Name column
                full_name = row.get('Full Name', "")
                if pd.isna(full_name) or str(full_name).strip() == "":
                    continue
                
                entity = {
                    "source": self.source,
                    "list_type": "Domestic TFS Kenya",
                    "full_name": str(full_name).strip(),
                }
                
                # Reference (KEi.001, KEi.002, etc.)
                if 'Reference' in df.columns and pd.notna(row.get('Reference')):
                    entity["entity_number"] = str(row['Reference']).strip()
                    entity["reference_number"] = str(row['Reference']).strip()
                else:
                    entity["entity_number"] = f"FRC-KE-{idx + 1:04d}"
                
                # Category (Individual/Entity)
                if 'Category' in df.columns and pd.notna(row.get('Category')):
                    category = str(row['Category']).strip()
                    if 'individual' in category.lower():
                        entity["entity_type"] = "Individual"
                    elif 'entity' in category.lower():
                        entity["entity_type"] = "Entity"
                    else:
                        entity["entity_type"] = category
                else:
                    entity["entity_type"] = "Unknown"
                
                # Title
                if 'Title' in df.columns and pd.notna(row.get('Title')):
                    title = str(row['Title']).strip()
                    if title.lower() != 'n/a':
                        entity["title"] = title
                
                # Aliases - parse multiple aliases separated by newlines/numbers
                if 'Aliases' in df.columns and pd.notna(row.get('Aliases')):
                    aliases_text = str(row['Aliases']).strip()
                    if aliases_text.lower() != 'n/a':
                        # Split by newlines and clean up numbered list format
                        alias_list = []
                        for line in aliases_text.split('\n'):
                            line = line.strip()
                            # Remove numbering like "1. ", "2. ", etc.
                            if line and len(line) > 3:
                                cleaned = line.split('.', 1)[-1].strip() if '.' in line[:5] else line
                                if cleaned and cleaned.lower() != 'n/a':
                                    alias_list.append({"name": cleaned, "type": "a.k.a."})
                        
                        if alias_list:
                            entity["aliases"] = alias_list
                
                # ID Number (map to national_id)
                if 'ID Number' in df.columns and pd.notna(row.get('ID Number')):
                    id_num = str(row['ID Number']).strip()
                    if id_num.lower() != 'n/a':
                        entity["national_id"] = id_num
                
                # Passport Number
                if 'Passport Number' in df.columns and pd.notna(row.get('Passport Number')):
                    passport = str(row['Passport Number']).strip()
                    if passport.lower() != 'n/a':
                        entity["passport_number"] = passport
                
                # Gender
                if 'Gender' in df.columns and pd.notna(row.get('Gender')):
                    gender = str(row['Gender']).strip()
                    if gender.lower() != 'n/a':
                        entity["gender"] = gender
                
                # Date of Birth
                if 'Date of Birth' in df.columns and pd.notna(row.get('Date of Birth')):
                    dob = str(row['Date of Birth']).strip()
                    if dob.lower() != 'n/a':
                        entity["date_of_birth"] = dob
                
                # Alternative Date of Birth
                if 'Alternative Date of Birth' in df.columns and pd.notna(row.get('Alternative Date of Birth')):
                    alt_dob = str(row['Alternative Date of Birth']).strip()
                    if alt_dob.lower() != 'n/a':
                        entity["alternative_dob"] = alt_dob
                
                # Place of Birth
                if 'Place of Birth' in df.columns and pd.notna(row.get('Place of Birth')):
                    pob = str(row['Place of Birth']).strip()
                    if pob.lower() != 'n/a':
                        entity["place_of_birth"] = pob
                
                # Nationality 1 (primary)
                if 'Nationality 1' in df.columns and pd.notna(row.get('Nationality 1')):
                    nat1 = str(row['Nationality 1']).strip()
                    if nat1.lower() != 'n/a':
                        entity["nationality"] = nat1
                        entity["country"] = nat1
                
                # Nationality 2 (secondary)
                if 'Nationality 2' in df.columns and pd.notna(row.get('Nationality 2')):
                    nat2 = str(row['Nationality 2']).strip()
                    if nat2.lower() != 'n/a':
                        entity["nationality_2"] = nat2
                
                # Physical Address
                if 'Physical Address' in df.columns and pd.notna(row.get('Physical Address')):
                    phys_addr = str(row['Physical Address']).strip()
                    if phys_addr.lower() != 'n/a':
                        entity["address"] = phys_addr
                
                # Postal Address (append to address if exists)
                if 'Postal Address' in df.columns and pd.notna(row.get('Postal Address')):
                    postal_addr = str(row['Postal Address']).strip()
                    if postal_addr.lower() != 'n/a':
                        if entity.get("address"):
                            entity["address"] = f"{entity['address']} | Postal: {postal_addr}"
                        else:
                            entity["address"] = f"Postal: {postal_addr}"
                
                # Occupation
                if 'Occupation' in df.columns and pd.notna(row.get('Occupation')):
                    occupation = str(row['Occupation']).strip()
                    if occupation.lower() != 'n/a':
                        # Add occupation to remarks
                        occupation_note = f"Occupation: {occupation}"
                        if entity.get("remarks"):
                            entity["remarks"] = f"{entity['remarks']} | {occupation_note}"
                        else:
                            entity["remarks"] = occupation_note
                
                # Telephone Number (add to remarks)
                if 'Telephone Number' in df.columns and pd.notna(row.get('Telephone Number')):
                    phone = str(row['Telephone Number']).strip()
                    if phone.lower() != 'n/a':
                        phone_note = f"Phone: {phone}"
                        if entity.get("remarks"):
                            entity["remarks"] = f"{entity['remarks']} | {phone_note}"
                        else:
                            entity["remarks"] = phone_note
                
                # Date of Designation (add to remarks as it's important info)
                if 'Date of Designation' in df.columns and pd.notna(row.get('Date of Designation')):
                    designation_date = str(row['Date of Designation']).strip()
                    if designation_date.lower() != 'n/a':
                        designation_note = f"Designated: {designation_date}"
                        if entity.get("remarks"):
                            entity["remarks"] = f"{designation_note} | {entity['remarks']}"
                        else:
                            entity["remarks"] = designation_note
                
                # Narrative Summary (main reason for designation)
                if 'Narrative Summary' in df.columns and pd.notna(row.get('Narrative Summary')):
                    narrative = str(row['Narrative Summary']).strip()
                    if narrative.lower() != 'n/a':
                        # Append narrative to existing remarks
                        if entity.get("remarks"):
                            entity["remarks"] = f"{entity['remarks']} | Summary: {narrative}"
                        else:
                            entity["remarks"] = narrative
                
                # Gender and other metadata (add to remarks for completeness)
                metadata_parts = []
                if 'Gender' in df.columns and pd.notna(row.get('Gender')):
                    gender = str(row['Gender']).strip()
                    if gender.lower() != 'n/a':
                        metadata_parts.append(f"Gender: {gender}")
                
                if 'Alternative Date of Birth' in df.columns and pd.notna(row.get('Alternative Date of Birth')):
                    alt_dob = str(row['Alternative Date of Birth']).strip()
                    if alt_dob.lower() != 'n/a':
                        metadata_parts.append(f"Alt DOB: {alt_dob}")
                
                if 'Nationality 2' in df.columns and pd.notna(row.get('Nationality 2')):
                    nat2 = str(row['Nationality 2']).strip()
                    if nat2.lower() != 'n/a':
                        metadata_parts.append(f"2nd Nationality: {nat2}")
                
                if 'Title' in df.columns and pd.notna(row.get('Title')):
                    title = str(row['Title']).strip()
                    if title.lower() != 'n/a':
                        metadata_parts.append(f"Title: {title}")
                
                if metadata_parts:
                    metadata_str = " | ".join(metadata_parts)
                    if entity.get("remarks"):
                        entity["remarks"] = f"{entity['remarks']} | {metadata_str}"
                    else:
                        entity["remarks"] = metadata_str
                
                # Last Update On is handled by list_updated_date automatically
                
                # Create search text including aliases
                entity["search_text"] = self._create_search_text(entity)
                
                entities.append(entity)
            
            logger.info(f"Parsed {len(entities)} entities from FRC Kenya list")
            return entities
            
        except Exception as e:
            logger.error(f"Error parsing FRC Kenya Excel: {str(e)}")
            raise
    
    def _create_search_text(self, entity: Dict) -> str:
        """Create searchable text from entity data including aliases (truncated to fit index limits)"""
        parts = [
            entity.get("full_name", ""),
            entity.get("nationality", ""),
            entity.get("country", ""),
            entity.get("place_of_birth", ""),
        ]
        
        # Add aliases to search text
        if entity.get("aliases"):
            for alias in entity["aliases"]:
                parts.append(alias.get("name", ""))
        
        # PostgreSQL btree index limit is ~2704 bytes
        # Truncate to 500 chars (max ~2000 bytes with UTF-8) to be safe
        search_text = " ".join([p for p in parts if p]).lower()
        return search_text[:500] if len(search_text) > 500 else search_text
    
    def save_to_database(self, entities: List[Dict]) -> Dict[str, int]:
        """Save FRC Kenya entities to database"""
        
        # Create update log
        log = ListUpdateLog(
            source=self.source,
            update_started=datetime.utcnow(),
            status="In Progress"
        )
        self.db.add(log)
        self.db.commit()
        
        stats = {"added": 0, "updated": 0, "total": len(entities)}
        
        try:
            for entity in entities:
                # Check for existing entries by name and source
                existing = self.db.query(SanctionsList).filter(
                    SanctionsList.source == self.source,
                    SanctionsList.full_name == entity.get("full_name")
                ).first()
                
                # Prepare entity data
                entity_data = {
                    "source": entity.get("source"),
                    "list_type": entity.get("list_type"),
                    "entity_type": entity.get("entity_type"),
                    "entity_number": entity.get("entity_number"),
                    "reference_number": entity.get("reference_number"),
                    "full_name": entity.get("full_name"),
                    "first_name": entity.get("first_name"),
                    "last_name": entity.get("last_name"),
                    "aliases": entity.get("aliases"),
                    "nationality": entity.get("nationality"),
                    "country": entity.get("country"),
                    "date_of_birth": entity.get("date_of_birth"),
                    "place_of_birth": entity.get("place_of_birth"),
                    "passport_number": entity.get("passport_number"),
                    "national_id": entity.get("national_id"),
                    "address": entity.get("address"),
                    "city": entity.get("city"),
                    "postal_code": entity.get("postal_code"),
                    "remarks": entity.get("remarks"),
                    "search_text": entity.get("search_text")
                }
                
                if existing:
                    # Update existing record
                    for key, value in entity_data.items():
                        if value is not None:
                            setattr(existing, key, value)
                    existing.list_updated_date = datetime.utcnow()
                    stats["updated"] += 1
                else:
                    # Add new record
                    entity = SanctionsList(**entity_data)
                    entity.list_updated_date = datetime.utcnow()
                    self.db.add(entity)
                    stats["added"] += 1
            
            self.db.commit()
            
            log.status = "Success"
            log.update_completed = datetime.utcnow()
            log.records_added = stats["added"]
            log.records_updated = stats["updated"]
            self.db.commit()
            
            logger.info(f"FRC Kenya list updated: {stats['added']} added, {stats['updated']} updated")
            return stats
            
        except Exception as e:
            log.status = "Failed"
            log.error_message = str(e)
            log.update_completed = datetime.utcnow()
            self.db.commit()
            logger.error(f"Error saving FRC Kenya data: {str(e)}")
            raise
