"""
Migration script to update PEP table field lengths
Run this to fix the "value too long" error for position field
"""

from sqlalchemy import create_engine, text
from config import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Update pep_lists table to handle longer position descriptions"""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    
    migrations = [
        # Change position from VARCHAR(300) to TEXT
        "ALTER TABLE pep_lists ALTER COLUMN position TYPE TEXT;",
        
        # Change organization from VARCHAR(300) to VARCHAR(500)
        "ALTER TABLE pep_lists ALTER COLUMN organization TYPE VARCHAR(500);"
    ]
    
    try:
        with engine.begin() as conn:
            for migration_sql in migrations:
                logger.info(f"Executing: {migration_sql}")
                conn.execute(text(migration_sql))
                logger.info("✓ Success")
        
        logger.info("\n✅ Migration completed successfully!")
        logger.info("You can now upload PEP lists with longer position descriptions.")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("PEP Table Migration")
    print("=" * 60)
    print("\nThis will update the database schema to support longer")
    print("position descriptions in the PEP lists table.")
    print("\nChanges:")
    print("  - position: VARCHAR(300) → TEXT (unlimited)")
    print("  - organization: VARCHAR(300) → VARCHAR(500)")
    print("=" * 60)
    
    response = input("\nProceed with migration? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        migrate_database()
    else:
        print("Migration cancelled.")
