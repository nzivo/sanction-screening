from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, JSON, Index
from sqlalchemy.sql import func
from database import Base


class SanctionsList(Base):
    """Stores all sanctions list entries from various sources"""
    __tablename__ = "sanctions_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, index=True)  # OFAC, UN, EU, UK, etc.
    list_type = Column(String(100), nullable=False)  # SDN, Consolidated, etc.
    entity_type = Column(String(50))  # Individual, Entity, Vessel, Aircraft
    
    # Name fields
    full_name = Column(String(500), nullable=False, index=True)
    first_name = Column(String(200))
    middle_name = Column(String(200))
    last_name = Column(String(200))
    aliases = Column(JSON)  # Array of alternative names
    
    # Identifiers
    entity_number = Column(String(100), index=True)
    reference_number = Column(String(100))
    
    # Additional information
    date_of_birth = Column(String(100))
    place_of_birth = Column(String(200))
    nationality = Column(String(100))
    citizenship = Column(String(100))
    passport_number = Column(String(100))
    national_id = Column(String(100))
    tax_id = Column(String(100))
    
    # Address information
    address = Column(Text)
    city = Column(String(200))
    country = Column(String(100), index=True)
    postal_code = Column(String(20))
    
    # Program/Sanction details
    programs = Column(JSON)  # Array of sanction programs
    remarks = Column(Text)
    
    # Metadata
    added_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, onupdate=func.now())
    list_updated_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Full text search
    search_text = Column(Text, index=True)  # Concatenated searchable text
    
    __table_args__ = (
        Index('idx_name_search', 'full_name', 'source'),
        Index('idx_country_source', 'country', 'source'),
    )


class PEPList(Base):
    """Politically Exposed Persons list"""
    __tablename__ = "pep_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    country = Column(String(100), nullable=False, index=True)
    
    # Name fields
    full_name = Column(String(500), nullable=False, index=True)
    first_name = Column(String(200))
    middle_name = Column(String(200))
    last_name = Column(String(200))
    aliases = Column(JSON)
    
    # PEP specific
    position = Column(Text)  # Government position/title (increased from 300 to support long descriptions)
    position_level = Column(String(50))  # National, Regional, Local
    organization = Column(String(500))  # Ministry, Department, etc.
    pep_type = Column(String(50))  # Direct, Family, Close Associate
    related_pep = Column(String(500))  # If family/associate, who's the main PEP
    
    # Additional info
    date_of_birth = Column(String(100))
    place_of_birth = Column(String(200))
    nationality = Column(String(100))
    
    # Status
    status = Column(String(50))  # Active, Former
    start_date = Column(String(100))
    end_date = Column(String(100))
    
    # Source
    source = Column(String(200))  # Where the PEP info came from
    source_url = Column(String(500))
    
    # Metadata
    added_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Risk assessment
    risk_level = Column(String(20))  # High, Medium, Low
    notes = Column(Text)
    
    __table_args__ = (
        Index('idx_pep_country_name', 'country', 'full_name'),
    )


class ScreeningResult(Base):
    """Stores screening query results"""
    __tablename__ = "screening_results"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Query information
    query_name = Column(String(500), nullable=False, index=True)
    query_type = Column(String(50))  # Individual, Entity, Vessel
    query_metadata = Column(JSON)  # Additional query parameters
    
    # Match information
    matched_list_id = Column(Integer)  # FK to sanctions_lists or pep_lists
    matched_list_type = Column(String(20), index=True)  # sanctions, pep
    matched_source = Column(String(50), index=True)  # OFAC, UN, PEP_KE, etc.
    matched_name = Column(String(500))
    
    # Matching details
    match_score = Column(Float, nullable=False, index=True)  # Fuzzy match percentage
    match_type = Column(String(50))  # Exact, Fuzzy, Alias
    matching_algorithm = Column(String(50))  # RapidFuzz, Exact, etc.
    
    # Match details breakdown
    name_match_score = Column(Float)
    dob_match = Column(Boolean)
    country_match = Column(Boolean)
    additional_matches = Column(JSON)  # Other matching fields
    
    # Decision
    status = Column(String(50), default="Pending")  # Pending, False Positive, True Match, Cleared
    reviewed_by = Column(String(200))
    review_date = Column(DateTime)
    review_notes = Column(Text)
    
    # Metadata
    screened_date = Column(DateTime, server_default=func.now(), index=True)
    client_reference = Column(String(200), index=True)  # External reference ID
    
    __table_args__ = (
        Index('idx_query_score', 'query_name', 'match_score'),
        Index('idx_date_source', 'screened_date', 'matched_source'),
    )


class ListUpdateLog(Base):
    """Tracks when sanctions lists were last updated"""
    __tablename__ = "list_update_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, index=True)
    list_type = Column(String(100))
    
    update_started = Column(DateTime, server_default=func.now())
    update_completed = Column(DateTime)
    
    status = Column(String(50))  # Success, Failed, In Progress
    records_added = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_deleted = Column(Integer, default=0)
    
    error_message = Column(Text)
    
    __table_args__ = (
        Index('idx_source_date', 'source', 'update_completed'),
    )
