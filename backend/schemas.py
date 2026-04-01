from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


# Screening Schemas
class ScreeningRequest(BaseModel):
    name: str = Field(..., description="Name to screen")
    entity_type: Optional[str] = Field(
        None, 
        description="Entity type: 'individual', 'entity', 'vessel', or leave empty to search all types"
    )
    country: Optional[str] = Field(None, description="Country for filtering (leave empty to search all countries)")
    date_of_birth: Optional[str] = Field(None, description="Date of birth for additional matching")
    client_reference: Optional[str] = Field(None, description="External reference ID")
    include_pep: bool = Field(True, description="Include PEP screening")
    include_sanctions: bool = Field(True, description="Include sanctions screening")


class BatchScreeningRequest(BaseModel):
    names: List[str] = Field(..., description="List of names to screen")
    entity_type: Optional[str] = None
    country: Optional[str] = None
    date_of_birth: Optional[str] = None
    client_reference: Optional[str] = None
    include_pep: bool = True
    include_sanctions: bool = True


class ScreeningResponse(BaseModel):
    query_name: str
    query_type: Optional[str]
    sanctions_matches: List[Dict]
    pep_matches: List[Dict]
    near_misses: Optional[List[Dict]] = []
    total_matches: int
    highest_score: float
    screening_date: str
    threshold_used: Optional[int] = None
    total_records_checked: Optional[int] = None


# PEP Schemas
class PEPCreate(BaseModel):
    country: str
    full_name: str
    position: str
    position_level: Optional[str] = None
    organization: Optional[str] = None
    pep_type: str = "Direct"
    related_pep: Optional[str] = None
    date_of_birth: Optional[str] = None
    place_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    status: str = "Active"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    source: str = "Manual Entry"
    source_url: Optional[str] = None
    risk_level: str = "Medium"
    notes: Optional[str] = None
    aliases: Optional[List[Dict]] = []


class PEPUpdate(BaseModel):
    full_name: Optional[str] = None
    position: Optional[str] = None
    position_level: Optional[str] = None
    organization: Optional[str] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None
    notes: Optional[str] = None


class PEPResponse(BaseModel):
    id: int
    country: str
    full_name: str
    position: str
    position_level: Optional[str]
    organization: Optional[str]
    pep_type: str
    status: str
    risk_level: Optional[str]
    is_active: bool
    added_date: datetime

    class Config:
        from_attributes = True


class PEPBulkUploadResponse(BaseModel):
    """Response for bulk PEP upload operations"""
    total_records: int
    added: int
    updated: int
    failed: int
    errors: Optional[List[str]] = []
    message: str


# World Bank Schemas
class WorldBankEntityResponse(BaseModel):
    """Response schema for World Bank debarred entity"""
    id: int
    full_name: str
    entity_type: Optional[str]
    country: Optional[str]
    address: Optional[str]
    from_date: Optional[str] = Field(None, alias="remarks")  # Debarment start date often in remarks
    to_date: Optional[str] = None  # Debarment end date
    grounds: Optional[str] = None  # Grounds for debarment
    entity_number: Optional[str]
    is_active: bool
    list_updated_date: Optional[datetime]
    added_date: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class WorldBankBulkUploadResponse(BaseModel):
    """Response for bulk World Bank entity upload"""
    total_records: int
    added: int
    updated: int
    failed: int
    errors: Optional[List[str]] = []
    message: str


# List Update Schemas
class ListUpdateResponse(BaseModel):
    source: str
    list_type: str
    records_added: int
    records_updated: int
    status: str
    update_completed: Optional[datetime]


# Screening History Schema
class ScreeningHistoryRequest(BaseModel):
    query_name: Optional[str] = None
    client_reference: Optional[str] = None
    min_score: Optional[float] = None
    limit: int = 100
