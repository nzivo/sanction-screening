from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging
import pandas as pd
import io

from database import get_db, engine, Base
from schemas import (
    ScreeningRequest, ScreeningResponse, BatchScreeningRequest,
    PEPCreate, PEPUpdate, PEPResponse, PEPBulkUploadResponse, ListUpdateResponse,
    WorldBankEntityResponse, WorldBankBulkUploadResponse,
    ScreeningHistoryRequest
)
from screening_service import ScreeningService
from pep_manager import PEPManager, initialize_kenya_peps
from worldbank_manager import WorldBankManager
from list_downloaders import OFACDownloader, UNDownloader, EUDownloader, UKDownloader, FRCKenyaDownloader
from ofac_csv_downloader import OFACCSVDownloader
from update_scheduler import UpdateScheduler
from config import get_settings

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Sanctions Screening API",
    description="Comprehensive sanctions and PEP screening service with OFAC, UN, and other lists",
    version="1.0.0"
)

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Health check
@app.get("/")
def root():
    return {
        "service": "Sanctions Screening API",
        "version": "1.0.0",
        "status": "active"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Screening Endpoints
@app.post("/screen", response_model=ScreeningResponse)
def screen_name(
    request: ScreeningRequest,
    db: Session = Depends(get_db)
):
    """
    Screen a name against sanctions and PEP lists
    """
    try:
        screening_service = ScreeningService(db, threshold=settings.fuzzy_match_threshold)
        result = screening_service.screen_name(
            name=request.name,
            entity_type=request.entity_type,
            country=request.country,
            date_of_birth=request.date_of_birth,
            client_reference=request.client_reference,
            include_pep=request.include_pep,
            include_sanctions=request.include_sanctions
        )
        return result
    except Exception as e:
        logger.error(f"Error screening name: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/screen/batch")
def batch_screen_names(
    request: BatchScreeningRequest,
    db: Session = Depends(get_db)
):
    """
    Screen multiple names at once
    """
    try:
        screening_service = ScreeningService(db, threshold=settings.fuzzy_match_threshold)
        results = screening_service.batch_screen(
            names=request.names,
            entity_type=request.entity_type,
            country=request.country,
            date_of_birth=request.date_of_birth,
            client_reference=request.client_reference,
            include_pep=request.include_pep,
            include_sanctions=request.include_sanctions
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"Error batch screening: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/screen/history")
def get_screening_history(
    request: ScreeningHistoryRequest,
    db: Session = Depends(get_db)
):
    """
    Get screening history with optional filters
    """
    try:
        screening_service = ScreeningService(db)
        results = screening_service.get_screening_history(
            query_name=request.query_name,
            client_reference=request.client_reference,
            min_score=request.min_score,
            limit=request.limit
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# PEP Management Endpoints
@app.post("/pep", response_model=PEPResponse)
def create_pep(
    pep: PEPCreate,
    db: Session = Depends(get_db)
):
    """
    Add a new PEP to the database
    """
    try:
        manager = PEPManager(db)
        result = manager.add_pep(**pep.model_dump())
        return result
    except Exception as e:
        logger.error(f"Error creating PEP: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pep/stats")
def get_pep_stats(db: Session = Depends(get_db)):
    """Get statistics about PEP database"""
    from sqlalchemy import func
    from models import PEPList
    
    total = db.query(func.count(PEPList.id)).filter(
        PEPList.is_active == True
    ).scalar()
    
    # Country breakdown
    country_counts = db.query(
        PEPList.country,
        func.count(PEPList.id).label('count')
    ).filter(
        PEPList.is_active == True
    ).group_by(PEPList.country).order_by(func.count(PEPList.id).desc()).limit(10).all()
    
    # Risk level breakdown
    risk_counts = db.query(
        PEPList.risk_level,
        func.count(PEPList.id).label('count')
    ).filter(
        PEPList.is_active == True
    ).group_by(PEPList.risk_level).all()
    
    return {
        "count": total,
        "total_active": total,
        "top_countries": [{"country": c[0] or "Unknown", "count": c[1]} for c in country_counts],
        "risk_levels": [{"level": r[0] or "Not Specified", "count": r[1]} for r in risk_counts]
    }


@app.get("/pep/{pep_id}", response_model=PEPResponse)
def get_pep(
    pep_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a PEP by ID
    """
    manager = PEPManager(db)
    pep = manager.get_pep_by_id(pep_id)
    
    if not pep:
        raise HTTPException(status_code=404, detail="PEP not found")
    
    return pep


@app.put("/pep/{pep_id}", response_model=PEPResponse)
def update_pep(
    pep_id: int,
    pep_update: PEPUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing PEP
    """
    try:
        manager = PEPManager(db)
        result = manager.update_pep(pep_id, **pep_update.model_dump(exclude_none=True))
        
        if not result:
            raise HTTPException(status_code=404, detail="PEP not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating PEP: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/pep/{pep_id}")
def deactivate_pep(
    pep_id: int,
    db: Session = Depends(get_db)
):
    """
    Deactivate a PEP (soft delete)
    """
    try:
        manager = PEPManager(db)
        success = manager.deactivate_pep(pep_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="PEP not found")
        
        return {"message": "PEP deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating PEP: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pep/country/{country}", response_model=List[PEPResponse])
def get_peps_by_country(
    country: str,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all PEPs for a specific country
    """
    manager = PEPManager(db)
    peps = manager.get_peps_by_country(country, is_active)
    return peps


@app.get("/pep/search/", response_model=List[PEPResponse])
def search_peps(
    country: str = None,
    name: str = None,
    position: str = None,
    status: str = None,
    risk_level: str = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """
    Search PEPs with various filters
    """
    manager = PEPManager(db)
    peps = manager.search_peps(
        country=country,
        name=name,
        position=position,
        status=status,
        risk_level=risk_level,
        is_active=is_active
    )
    return peps


@app.post("/pep/initialize/kenya")
def initialize_kenya_pep_list(db: Session = Depends(get_db)):
    """
    Initialize Kenya PEP list with sample data
    """
    try:
        stats = initialize_kenya_peps(db)
        return {
            "message": "Kenya PEP list initialized",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error initializing Kenya PEPs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pep/upload", response_model=PEPBulkUploadResponse)
async def upload_pep_list(
    file: UploadFile = File(...),
    country: str = "Kenya",
    source: str = "Excel Upload",
    update_if_exists: bool = True,
    db: Session = Depends(get_db)
):
    """
    Upload PEP list from Excel file (.xlsx)
    
    Expected columns:
    - NAME (required): Full name of the PEP
    - ENTITY DESCRIPTION (required): Position/role
    - ENTITY SOURCE: Source type (optional, defaults to 'PEP')
    
    Additional optional columns that will be mapped if present:
    - ORGANIZATION, POSITION_LEVEL, RISK_LEVEL, STATUS, etc.
    """
    errors = []
    
    try:
        # Validate file extension
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(
                status_code=400,
                detail="Only .xlsx files are supported. Please upload an Excel file."
            )
        
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        logger.info(f"Uploaded file: {file.filename}, Rows: {len(df)}")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        # Validate required columns
        required_columns = ['NAME', 'ENTITY DESCRIPTION']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}. "
                       f"Available columns: {', '.join(df.columns.tolist())}"
            )
        
        # Convert to PEP data list
        pep_data_list = []
        
        for idx, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row['NAME']) or str(row['NAME']).strip() == '':
                    continue
                
                pep_data = {
                    'country': country,
                    'full_name': str(row['NAME']).strip(),
                    'position': str(row['ENTITY DESCRIPTION']).strip(),
                    'source': source,
                    'pep_type': 'Direct',
                    'status': 'Active',
                    'risk_level': 'Medium'
                }
                
                # Map optional columns if present
                column_mapping = {
                    'ORGANIZATION': 'organization',
                    'POSITION_LEVEL': 'position_level',
                    'RISK_LEVEL': 'risk_level',
                    'STATUS': 'status',
                    'PEP_TYPE': 'pep_type',
                    'NATIONALITY': 'nationality',
                    'DATE_OF_BIRTH': 'date_of_birth',
                    'PLACE_OF_BIRTH': 'place_of_birth',
                    'NOTES': 'notes'
                }
                
                for excel_col, pep_field in column_mapping.items():
                    if excel_col in df.columns and not pd.isna(row[excel_col]):
                        pep_data[pep_field] = str(row[excel_col]).strip()
                
                pep_data_list.append(pep_data)
                
            except Exception as e:
                error_msg = f"Row {idx + 2}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        if not pep_data_list:
            raise HTTPException(
                status_code=400,
                detail="No valid PEP records found in the uploaded file"
            )
        
        # Bulk add PEPs
        manager = PEPManager(db)
        stats = manager.bulk_add_peps(pep_data_list, update_if_exists=update_if_exists)
        
        return PEPBulkUploadResponse(
            total_records=len(df),
            added=stats['added'],
            updated=stats['updated'],
            failed=stats['failed'],
            errors=errors[:10] if errors else [],  # Return max 10 errors
            message=f"Successfully processed {stats['added'] + stats['updated']} PEPs "
                   f"({stats['added']} new, {stats['updated']} updated, {stats['failed']} failed)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading PEP list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


# World Bank Debarred Entities Management
@app.post("/worldbank/upload", response_model=WorldBankBulkUploadResponse)
async def upload_worldbank_list(
    file: UploadFile = File(...),
    update_if_exists: bool = True,
    db: Session = Depends(get_db)
):
    """
    Upload World Bank debarred entities list (Excel or CSV)
    
    Required columns:
    - Firm Name (or Name)
    - Country
    - Ineligibility Period From
    
    Optional columns:
    - Ineligibility Period To
    - Grounds
    - Address
    - Entity Type
    
    Args:
        file: Excel (.xlsx) or CSV file with World Bank debarred entities
        update_if_exists: Update existing entries if found (default: True)
    
    Returns:
        Upload statistics and any errors
    """
    errors = []
    
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file extension
        file_ext = file.filename.lower().split('.')[-1]
        if file_ext not in ['xlsx', 'xls', 'csv']:
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Please upload Excel (.xlsx, .xls) or CSV (.csv) file"
            )
        
        # Read file
        contents = await file.read()
        
        if file_ext == 'csv':
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        logger.info(f"Uploaded file: {file.filename}, Rows: {len(df)}")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        # Try to identify name column (various formats)
        name_column = None
        for col in ['Firm Name', 'Name', 'FIRM NAME', 'NAME', 'Entity Name', 'ENTITY NAME']:
            if col in df.columns:
                name_column = col
                break
        
        if not name_column:
            raise HTTPException(
                status_code=400,
                detail=f"Could not find name column. Expected 'Firm Name' or 'Name'. "
                       f"Available columns: {', '.join(df.columns.tolist())}"
            )
        
        # Convert to World Bank entity data list
        entity_data_list = []
        
        for idx, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row[name_column]) or str(row[name_column]).strip() == '':
                    continue
                
                # Base entity data
                entity_data = {
                    'source': 'WorldBank',
                    'list_type': 'Debarred',
                    'entity_type': 'Entity',  # Default to Entity (firms)
                    'full_name': str(row[name_column]).strip(),
                }
                
                # Map columns with various possible names
                column_mappings = {
                    'country': ['Country', 'COUNTRY', 'Country of Origin'],
                    'address': ['Address', 'ADDRESS'],
                    'entity_type': ['Entity Type', 'ENTITY TYPE', 'Type'],
                }
                
                # Apply mappings
                for field, possible_cols in column_mappings.items():
                    for col in possible_cols:
                        if col in df.columns and not pd.isna(row[col]):
                            entity_data[field] = str(row[col]).strip()
                            break
                
                # Handle dates and grounds (stored in remarks for now)
                remarks_parts = []
                
                for date_col in ['Ineligibility Period From', 'From Date', 'FROM DATE', 'Start Date']:
                    if date_col in df.columns and not pd.isna(row[date_col]):
                        remarks_parts.append(f"From: {row[date_col]}")
                        break
                
                for date_col in ['Ineligibility Period To', 'To Date', 'TO DATE', 'End Date']:
                    if date_col in df.columns and not pd.isna(row[date_col]):
                        remarks_parts.append(f"To: {row[date_col]}")
                        break
                
                for grounds_col in ['Grounds', 'GROUNDS', 'Reason', 'Basis']:
                    if grounds_col in df.columns and not pd.isna(row[grounds_col]):
                        remarks_parts.append(f"Grounds: {row[grounds_col]}")
                        break
                
                if remarks_parts:
                    entity_data['remarks'] = '; '.join(remarks_parts)
                
                # Generate entity number from index or use provided
                if 'ID' in df.columns and not pd.isna(row['ID']):
                    entity_data['entity_number'] = str(row['ID'])
                else:
                    entity_data['entity_number'] = f"WB_{idx + 1}"
                
                # Create searchable text
                search_parts = [entity_data['full_name']]
                if entity_data.get('country'):
                    search_parts.append(entity_data['country'])
                if entity_data.get('address'):
                    search_parts.append(entity_data['address'])
                entity_data['search_text'] = ' '.join(search_parts).lower()
                
                entity_data_list.append(entity_data)
                
            except Exception as e:
                error_msg = f"Row {idx + 2}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        if not entity_data_list:
            raise HTTPException(
                status_code=400,
                detail="No valid World Bank entities found in the uploaded file"
            )
        
        # Bulk add entities
        manager = WorldBankManager(db)
        stats = manager.bulk_add_entities(entity_data_list, update_if_exists=update_if_exists)
        
        return WorldBankBulkUploadResponse(
            total_records=len(df),
            added=stats['added'],
            updated=stats['updated'],
            failed=stats['failed'],
            errors=errors[:10] if errors else [],
            message=f"Successfully processed {stats['added'] + stats['updated']} entities "
                   f"({stats['added']} new, {stats['updated']} updated, {stats['failed']} failed)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading World Bank list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.get("/worldbank", response_model=List[WorldBankEntityResponse])
def get_worldbank_entities(
    name: Optional[str] = None,
    country: Optional[str] = None,
    is_active: bool = True,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get World Bank debarred entities with optional filtering
    
    Args:
        name: Filter by name (partial match)
        country: Filter by country
        is_active: Filter by active status
        limit: Maximum number of results
    """
    manager = WorldBankManager(db)
    entities = manager.search_entities(
        name=name,
        country=country,
        is_active=is_active,
        limit=limit
    )
    return entities


@app.get("/worldbank/stats")
def get_worldbank_stats(db: Session = Depends(get_db)):
    """Get statistics about World Bank debarred entities"""
    manager = WorldBankManager(db)
    
    total = manager.get_count(is_active=True)
    inactive = manager.get_count(is_active=False)
    
    # Get country breakdown
    from sqlalchemy import func
    from models import SanctionsList
    
    country_counts = db.query(
        SanctionsList.country,
        func.count(SanctionsList.id).label('count')
    ).filter(
        SanctionsList.source == 'WorldBank',
        SanctionsList.is_active == True
    ).group_by(SanctionsList.country).order_by(func.count(SanctionsList.id).desc()).limit(10).all()
    
    return {
        "count": total,
        "total_active": total,
        "total_inactive": inactive,
        "top_countries": [{"country": c[0] or "Unknown", "count": c[1]} for c in country_counts]
    }


@app.get("/worldbank/{entity_id}", response_model=WorldBankEntityResponse)
def get_worldbank_entity(
    entity_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific World Bank entity by ID"""
    manager = WorldBankManager(db)
    entity = manager.get_entity_by_id(entity_id)
    
    if not entity:
        raise HTTPException(status_code=404, detail="World Bank entity not found")
    
    return entity


@app.delete("/worldbank/{entity_id}")
def delete_worldbank_entity(
    entity_id: int,
    db: Session = Depends(get_db)
):
    """Delete a World Bank entity"""
    manager = WorldBankManager(db)
    
    if manager.delete_entity(entity_id):
        return {"message": f"World Bank entity {entity_id} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="World Bank entity not found")


@app.post("/worldbank/{entity_id}/deactivate")
def deactivate_worldbank_entity(
    entity_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate a World Bank entity"""
    manager = WorldBankManager(db)
    
    if manager.deactivate_entity(entity_id):
        return {"message": f"World Bank entity {entity_id} deactivated successfully"}
    else:
        raise HTTPException(status_code=404, detail="World Bank entity not found")


# FRC Kenya Management Endpoints
@app.post("/frc-kenya/upload")
async def upload_frc_kenya_list(
    file: UploadFile = File(...),
    update_if_exists: bool = True,
    db: Session = Depends(get_db)
):
    """
    Upload FRC Kenya domestic sanctions list manually from Excel file
    
    File should contain columns like:
    - Name (required)
    - Type or Entity Type
    - Nationality or Country
    - Passport or ID Number
    - Date of Birth
    - Address
    - Designation Date
    - Reason or Grounds
    
    Args:
        file: Excel file (.xlsx) with FRC Kenya list
        update_if_exists: Update existing entities if found
    """
    try:
        # Validate file type
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in ['xlsx', 'xls']:
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Please upload Excel (.xlsx, .xls) file"
            )
        
        # Read file
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        logger.info(f"Uploaded FRC Kenya file: {file.filename}, Rows: {len(df)}")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        # Process with FRC Kenya downloader parse logic
        downloader = FRCKenyaDownloader(db)
        entities = downloader._parse_excel(contents)
        
        if not entities:
            raise HTTPException(
                status_code=400,
                detail="No valid entities found in the uploaded file"
            )
        
        # Save to database
        stats = downloader.save_to_database(entities)
        
        return {
            "total_records": len(df),
            "added": stats['added'],
            "updated": stats['updated'],
            "message": f"Successfully processed {stats['added'] + stats['updated']} FRC Kenya entities "
                      f"({stats['added']} new, {stats['updated']} updated)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading FRC Kenya list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.get("/frc-kenya")
def get_frc_kenya_entities(
    name: Optional[str] = None,
    country: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get FRC Kenya domestic sanctions list entities
    
    Args:
        name: Filter by name (partial match)
        country: Filter by country
        entity_type: Filter by entity type (Individual/Entity)
        limit: Maximum number of results
    """
    from models import SanctionsList
    
    query = db.query(SanctionsList).filter(
        SanctionsList.source == "FRC_Kenya",
        SanctionsList.is_active == True
    )
    
    if name:
        query = query.filter(SanctionsList.full_name.ilike(f"%{name}%"))
    
    if country:
        query = query.filter(SanctionsList.country.ilike(f"%{country}%"))
    
    if entity_type:
        query = query.filter(SanctionsList.entity_type.ilike(f"%{entity_type}%"))
    
    entities = query.limit(limit).all()
    
    return [{
        "id": e.id,
        "entity_number": e.entity_number,
        "full_name": e.full_name,
        "entity_type": e.entity_type,
        "nationality": e.nationality,
        "country": e.country,
        "date_of_birth": e.date_of_birth,
        "passport_number": e.passport_number,
        "address": e.address,
        "remarks": e.remarks,
        "designation_date": e.designation_date,
        "list_updated_date": e.list_updated_date
    } for e in entities]


@app.get("/frc-kenya/stats")
def get_frc_kenya_stats(db: Session = Depends(get_db)):
    """Get statistics about FRC Kenya domestic list"""
    from sqlalchemy import func
    from models import SanctionsList
    
    total = db.query(func.count(SanctionsList.id)).filter(
        SanctionsList.source == "FRC_Kenya",
        SanctionsList.is_active == True
    ).scalar()
    
    # Entity type breakdown
    type_counts = db.query(
        SanctionsList.entity_type,
        func.count(SanctionsList.id).label('count')
    ).filter(
        SanctionsList.source == "FRC_Kenya",
        SanctionsList.is_active == True
    ).group_by(SanctionsList.entity_type).all()
    
    # Country breakdown
    country_counts = db.query(
        SanctionsList.country,
        func.count(SanctionsList.id).label('count')
    ).filter(
        SanctionsList.source == "FRC_Kenya",
        SanctionsList.is_active == True
    ).group_by(SanctionsList.country).order_by(func.count(SanctionsList.id).desc()).limit(10).all()
    
    return {
        "count": total,
        "total": total,
        "by_type": [{"type": t[0] or "Unknown", "count": t[1]} for t in type_counts],
        "top_countries": [{"country": c[0] or "Unknown", "count": c[1]} for c in country_counts]
    }


# Sanctions List Management Endpoints
def update_ofac_list_background(force: bool = False):
    """Background task to update OFAC list"""
    db = next(get_db())
    try:
        # Check if update is needed
        scheduler = UpdateScheduler(db)
        check = scheduler.should_update("OFAC", force=force)
        
        if not check["should_update"]:
            logger.info(f"Skipping OFAC update: {check['reason']}")
            return {"skipped": True, "reason": check["reason"]}
        
        logger.info(f"Starting OFAC list update: {check['reason']}")
        downloader = OFACDownloader(db)
        entities = downloader.download_sdn_list()
        stats = downloader.save_to_database(entities)
        logger.info(f"OFAC list updated: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error updating OFAC list: {str(e)}", exc_info=True)
        return {"error": str(e)}
    finally:
        db.close()


def update_un_list_background(force: bool = False):
    """Background task to update UN list"""
    db = next(get_db())
    try:
        # Check if update is needed
        scheduler = UpdateScheduler(db)
        check = scheduler.should_update("UN", force=force)
        
        if not check["should_update"]:
            logger.info(f"Skipping UN update: {check['reason']}")
            return {"skipped": True, "reason": check["reason"]}
        
        logger.info(f"Starting UN list update: {check['reason']}")
        downloader = UNDownloader(db)
        entities = downloader.download_consolidated_list()
        stats = downloader.save_to_database(entities)
        logger.info(f"UN list updated: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error updating UN list: {str(e)}", exc_info=True)
        return {"error": str(e)}
    finally:
        db.close()


def update_eu_list_background(force: bool = False):
    """Background task to update EU list"""
    db = next(get_db())
    try:
        # Check if update is needed
        scheduler = UpdateScheduler(db)
        check = scheduler.should_update("EU", force=force)
        
        if not check["should_update"]:
            logger.info(f"Skipping EU update: {check['reason']}")
            return {"skipped": True, "reason": check["reason"]}
        
        logger.info(f"Starting EU list update: {check['reason']}")
        downloader = EUDownloader(db)
        entities = downloader.download_sanctions_list()
        stats = downloader.save_to_database(entities)
        logger.info(f"EU list updated successfully: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error updating EU list: {str(e)}", exc_info=True)
        return {"error": str(e)}
    finally:
        db.close()


def update_uk_list_background(force: bool = False):
    """Background task to update UK list"""
    db = next(get_db())
    try:
        # Check if update is needed
        scheduler = UpdateScheduler(db)
        check = scheduler.should_update("UK", force=force)
        
        if not check["should_update"]:
            logger.info(f"Skipping UK update: {check['reason']}")
            return {"skipped": True, "reason": check["reason"]}
        
        logger.info(f"Starting UK list update: {check['reason']}")
        downloader = UKDownloader(db)
        entities = downloader.download_sanctions_list()
        stats = downloader.save_to_database(entities)
        logger.info(f"UK list updated successfully: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error updating UK list: {str(e)}", exc_info=True)
        return {"error": str(e)}
    finally:
        db.close()


def update_frc_kenya_list_background(force: bool = False):
    """Background task to update FRC Kenya domestic list"""
    db = next(get_db())
    try:
        # Check if update is needed
        scheduler = UpdateScheduler(db)
        check = scheduler.should_update("FRC_Kenya", force=force)
        
        if not check["should_update"]:
            logger.info(f"Skipping FRC Kenya update: {check['reason']}")
            return {"skipped": True, "reason": check["reason"]}
        
        logger.info(f"Starting FRC Kenya list update: {check['reason']}")
        downloader = FRCKenyaDownloader(db)
        entities = downloader.download_sanctions_list()
        stats = downloader.save_to_database(entities)
        logger.info(f"FRC Kenya list updated successfully: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error updating FRC Kenya list: {str(e)}", exc_info=True)
        return {"error": str(e)}
    finally:
        db.close()


@app.post("/lists/update/ofac")
def update_ofac_list(
    background_tasks: BackgroundTasks,
    force: bool = False
):
    """
    Trigger OFAC SDN list update (XML format)
    
    Args:
        force: Skip schedule check and force update
    """
    background_tasks.add_task(update_ofac_list_background, force)
    return {
        "message": "OFAC list update started in background",
        "source": "OFAC",
        "list_type": "SDN",
        "format": "XML",
        "forced": force
    }


@app.post("/lists/update/ofac-csv")
def update_ofac_csv(
    background_tasks: BackgroundTasks
):
    """
    Trigger OFAC SDN list update using CSV/TXT format (more reliable)
    """
    def update_csv():
        db = next(get_db())
        try:
            logger.info("Starting OFAC CSV list update...")
            downloader = OFACCSVDownloader(db)
            entities = downloader.download_sdn_list()
            stats = downloader.save_to_database(entities)
            logger.info(f"OFAC CSV list updated: {stats}")
        except Exception as e:
            logger.error(f"Error updating OFAC CSV list: {str(e)}", exc_info=True)
        finally:
            db.close()
    
    background_tasks.add_task(update_csv)
    return {
        "message": "OFAC CSV list update started in background",
        "source": "OFAC",
        "list_type": "SDN",
        "format": "CSV/TXT"
    }


@app.post("/lists/update/un")
def update_un_list(
    background_tasks: BackgroundTasks,
    force: bool = False
):
    """
    Trigger UN Consolidated list update
    
    Args:
        force: Skip schedule check and force update
    """
    background_tasks.add_task(update_un_list_background, force)
    return {
        "message": "UN list update started in background",
        "source": "UN",
        "list_type": "Consolidated",
        "forced": force
    }


@app.post("/lists/update/eu")
def update_eu_list(
    background_tasks: BackgroundTasks,
    force: bool = False
):
    """
    Trigger EU Financial Sanctions list update
    
    Args:
        force: Skip schedule check and force update
    """
    background_tasks.add_task(update_eu_list_background, force)
    return {
        "message": "EU list update started in background",
        "source": "EU",
        "list_type": "EU Sanctions",
        "forced": force
    }


@app.post("/lists/update/uk")
def update_uk_list(
    background_tasks: BackgroundTasks,
    force: bool = False
):
    """
    Trigger UK HM Treasury Consolidated list update
    
    Args:
        force: Skip schedule check and force update
    """
    background_tasks.add_task(update_uk_list_background, force)
    return {
        "message": "UK list update started in background",
        "source": "UK",
        "list_type": "UK Consolidated",
        "forced": force
    }


@app.post("/lists/update/frc-kenya")
def update_frc_kenya_list(
    background_tasks: BackgroundTasks,
    force: bool = False
):
    """
    Trigger FRC Kenya domestic sanctions list update
    
    Args:
        force: Skip schedule check and force update
    """
    background_tasks.add_task(update_frc_kenya_list_background, force)
    return {
        "message": "FRC Kenya list update started in background",
        "source": "FRC_Kenya",
        "list_type": "Domestic TFS Kenya",
        "forced": force
    }


@app.post("/lists/update/all")
def update_all_lists(
    background_tasks: BackgroundTasks,
    force: bool = False
):
    """
    Trigger update of all sanctions lists
    
    Args:
        force: Skip schedule checks and force all updates
    """
    background_tasks.add_task(update_ofac_list_background, force)
    background_tasks.add_task(update_un_list_background, force)
    background_tasks.add_task(update_eu_list_background, force)
    background_tasks.add_task(update_uk_list_background, force)
    background_tasks.add_task(update_frc_kenya_list_background, force)
    
    return {
        "message": "All lists update started in background",
        "lists": ["OFAC SDN", "UN Consolidated", "EU Sanctions", "UK Consolidated", "FRC Kenya Domestic"],
        "forced": force
    }


@app.get("/lists/check-updates")
def check_updates(db: Session = Depends(get_db)):
    """
    Check which lists need updating based on schedule
    
    Returns status for each list:
    - should_update: Whether update is recommended
    - reason: Why update is/isn't needed
    - last_update: When last successfully updated
    - hours_since_update: Hours since last update
    
    Also includes entity counts for all sources including World Bank and FRC Kenya
    """
    from sqlalchemy import func
    from models import SanctionsList
    
    scheduler = UpdateScheduler(db)
    status = scheduler.get_update_status()
    
    # Get entity counts for all sources
    entity_counts = {}
    all_sources = ["OFAC", "UN", "EU", "UK", "FRC_Kenya", "WorldBank"]
    
    for source in all_sources:
        count = db.query(func.count(SanctionsList.id)).filter(
            SanctionsList.source == source,
            SanctionsList.is_active == True
        ).scalar() or 0
        entity_counts[source] = count
    
    # Get last update times for World Bank and FRC Kenya (manual uploads)
    from models import ListUpdateLog
    
    worldbank_last = db.query(ListUpdateLog).filter(
        ListUpdateLog.source == "WorldBank"
    ).order_by(ListUpdateLog.update_started.desc()).first()
    
    frc_kenya_last = db.query(ListUpdateLog).filter(
        ListUpdateLog.source == "FRC_Kenya"
    ).order_by(ListUpdateLog.update_started.desc()).first()
    
    # Add World Bank info (manual upload only, no auto-update schedule)
    status["WorldBank"] = {
        "should_update": False,
        "reason": "Manual upload only - use POST /worldbank/upload endpoint",
        "last_update": worldbank_last.update_completed.isoformat() if worldbank_last and worldbank_last.update_completed else None,
        "entity_count": entity_counts["WorldBank"],
        "update_method": "manual"
    }
    
    # Enhance FRC Kenya status with entity count
    if "FRC_Kenya" in status:
        status["FRC_Kenya"]["entity_count"] = entity_counts["FRC_Kenya"]
    
    # Add entity counts to other sources
    for source in ["OFAC", "UN", "EU", "UK"]:
        if source in status:
            status[source]["entity_count"] = entity_counts[source]
    
    return {
        "check_time": datetime.utcnow().isoformat(),
        "sources": status,
        "summary": {
            "needs_update": [source for source, info in status.items() if info.get("should_update", False)],
            "up_to_date": [source for source, info in status.items() if not info.get("should_update", True)],
            "total_entities": sum(entity_counts.values()),
            "by_source": entity_counts
        }
    }


@app.get("/lists/schedule")
def get_update_schedule(db: Session = Depends(get_db)):
    """
    Get update schedule configuration and intervals
    """
    scheduler = UpdateScheduler(db)
    
    sources_info = {}
    for source in ["OFAC", "UN", "EU", "UK", "FRC_Kenya"]:
        last_update_info = scheduler.get_last_update_info(source)
        check = scheduler.should_update(source)
        
        sources_info[source] = {
            "update_interval_hours": scheduler.UPDATE_INTERVALS.get(source, 168),
            "min_interval_hours": scheduler.MIN_UPDATE_INTERVAL,
            "last_update": last_update_info,
            "should_update": check["should_update"],
            "reason": check["reason"]
        }
    
    # Add World Bank (manual only)
    from models import ListUpdateLog
    worldbank_last = db.query(ListUpdateLog).filter(
        ListUpdateLog.source == "WorldBank"
    ).order_by(ListUpdateLog.update_started.desc()).first()
    
    sources_info["WorldBank"] = {
        "update_interval_hours": None,
        "min_interval_hours": None,
        "last_update": {
            "update_started": worldbank_last.update_started.isoformat() if worldbank_last else None,
            "update_completed": worldbank_last.update_completed.isoformat() if worldbank_last and worldbank_last.update_completed else None,
            "status": worldbank_last.status if worldbank_last else None,
            "records_added": worldbank_last.records_added if worldbank_last else 0,
            "records_updated": worldbank_last.records_updated if worldbank_last else 0
        } if worldbank_last else None,
        "should_update": False,
        "reason": "Manual upload only"
    }
    
    return {
        "schedule": sources_info,
        "recommendations": {
            "OFAC": "Daily (highly dynamic, 2-5 updates/week)",
            "UN": "Weekly (changes every 2-4 weeks)",
            "EU": "Weekly (1-3 updates/month)",
            "UK": "Weekly (1-2 updates/month)",
            "FRC_Kenya": "Weekly (updates via TFS notices)",
            "WorldBank": "Manual upload only - no automated updates"
        }
    }


@app.get("/lists/status")
def get_lists_status(db: Session = Depends(get_db)):
    """
    Get status of all sanctions lists
    """
    from models import ListUpdateLog, SanctionsList
    from sqlalchemy import func
    
    # Get latest update logs
    logs = db.query(ListUpdateLog).order_by(ListUpdateLog.update_started.desc()).limit(10).all()
    
    # Get counts by source
    counts = db.query(
        SanctionsList.source,
        func.count(SanctionsList.id).label("count")
    ).filter(SanctionsList.is_active == True).group_by(SanctionsList.source).all()
    
    return {
        "recent_updates": [
            {
                "source": log.source,
                "list_type": log.list_type,
                "status": log.status,
                "records_added": log.records_added,
                "records_updated": log.records_updated,
                "update_completed": log.update_completed.isoformat() if log.update_completed else None
            }
            for log in logs
        ],
        "list_counts": {count[0]: count[1] for count in counts}
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
