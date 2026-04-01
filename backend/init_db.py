"""
Initialization script for the sanctions screening database
Run this after creating the database to set up tables and initial data
"""

from database import engine, Base, SessionLocal
from pep_manager import initialize_kenya_peps
from models import SanctionsList, PEPList, ScreeningResult, ListUpdateLog
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database with tables and seed data"""
    
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")
    
    # Initialize Kenya PEP list
    logger.info("Initializing Kenya PEP list...")
    db = SessionLocal()
    try:
        stats = initialize_kenya_peps(db)
        logger.info(f"Kenya PEP list initialized: {stats['added']} added, {stats['failed']} failed")
    except Exception as e:
        logger.error(f"Error initializing Kenya PEPs: {str(e)}")
    finally:
        db.close()
    
    logger.info("Database initialization complete!")
    logger.info("\nNext steps:")
    logger.info("1. Run the application: python main.py")
    logger.info("2. Update sanctions lists: POST /lists/update/all")
    logger.info("3. Start screening: POST /screen")


if __name__ == "__main__":
    init_database()
