#!/usr/bin/env python3
"""
Database Migration Script

This script migrates data from a local SQLite database (sceneweaver.db) 
to the PostgreSQL database configured in .env file.

The migration preserves all relationships and data integrity.
"""

import os
import sys
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, IntegrityError

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models import Base, User, Project, World, Character, StoryThread, Story, ScreenplayScene, StoryboardImage, AnimaticsScene
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles data migration from SQLite to PostgreSQL"""
    
    def __init__(self):
        self.sqlite_db_path = project_root / 'sceneweaver.db'
        self.postgres_url = os.getenv('POSTGRES_URL') or self._build_postgres_url()
        self.sqlite_engine = None
        self.postgres_engine = None
        self.sqlite_session = None
        self.postgres_session = None
        
    def _build_postgres_url(self):
        """Build PostgreSQL URL from environment variables"""
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        db = os.getenv('POSTGRES_DB', 'sceneweaver-mvp-db')
        user = os.getenv('POSTGRES_USER', 'sceneweaver_admin')
        password = os.getenv('POSTGRES_PASSWORD', 'admin')
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    def connect_to_databases(self):
        """Establish connections to both SQLite and PostgreSQL databases"""
        try:
            # Connect to SQLite
            if not self.sqlite_db_path.exists():
                logger.error(f"[ERROR] SQLite database not found at: {self.sqlite_db_path}")
                logger.error("Please ensure sceneweaver.db exists in the project root.")
                return False
                
            sqlite_url = f"sqlite:///{self.sqlite_db_path}"
            self.sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
            
            # Test SQLite connection
            with self.sqlite_engine.connect() as conn:
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.fetchone()[0]
                logger.info(f"[SUCCESS] Connected to SQLite version: {version}")
            
            # Create SQLite session
            SqliteSession = sessionmaker(bind=self.sqlite_engine)
            self.sqlite_session = SqliteSession()
            
            # Connect to PostgreSQL
            self.postgres_engine = create_engine(self.postgres_url)
            
            # Test PostgreSQL connection
            with self.postgres_engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                logger.info(f"[SUCCESS] Connected to PostgreSQL: {version[:50]}...")
            
            # Create PostgreSQL session
            PostgresSession = sessionmaker(bind=self.postgres_engine)
            self.postgres_session = PostgresSession()
            
            return True
            
        except OperationalError as e:
            logger.error(f"[ERROR] Database connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error connecting to databases: {e}")
            return False
    
    def ensure_postgres_tables_exist(self):
        """Ensure PostgreSQL tables exist before migration"""
        try:
            logger.info("Ensuring PostgreSQL tables exist...")
            Base.metadata.create_all(bind=self.postgres_engine)
            logger.info("[SUCCESS] PostgreSQL tables verified/created")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to create PostgreSQL tables: {e}")
            return False
    
    def get_table_counts(self):
        """Get record counts from both databases"""
        counts = {'sqlite': {}, 'postgres': {}}
        
        tables = ['Users', 'Projects', 'Worlds', 'Characters', 'StoryThreads', 
                 'Stories', 'ScreenplayScenes', 'StoryboardImages', 'AnimaticScenes']
        
        try:
            # SQLite counts
            for table in tables:
                result = self.sqlite_session.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                counts['sqlite'][table] = result.scalar() or 0
            
            # PostgreSQL counts
            for table in tables:
                result = self.postgres_session.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                counts['postgres'][table] = result.scalar() or 0
                
        except Exception as e:
            logger.warning(f"[WARNING] Could not get table counts: {e}")
            
        return counts
    
    def migrate_table(self, model_class, table_name):
        """Migrate data for a specific table"""
        try:
            logger.info(f"Migrating {table_name}...")
            
            # Get all records from SQLite
            sqlite_records = self.sqlite_session.query(model_class).all()
            
            if not sqlite_records:
                logger.info(f"  No records found in {table_name}")
                return True
            
            migrated_count = 0
            skipped_count = 0
            
            for record in sqlite_records:
                try:
                    # Check if record already exists in PostgreSQL
                    existing = self.postgres_session.query(model_class).filter_by(id=record.id).first()
                    
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Create new record in PostgreSQL
                    # Get all column values
                    record_dict = {}
                    for column in model_class.__table__.columns:
                        record_dict[column.name] = getattr(record, column.name)
                    
                    new_record = model_class(**record_dict)
                    self.postgres_session.add(new_record)
                    migrated_count += 1
                    
                except IntegrityError as e:
                    logger.warning(f"  [WARNING] Skipping duplicate record in {table_name}: {e}")
                    self.postgres_session.rollback()
                    skipped_count += 1
                    continue
            
            # Commit the batch
            self.postgres_session.commit()
            
            logger.info(f"  [SUCCESS] {table_name}: {migrated_count} migrated, {skipped_count} skipped")
            return True
            
        except Exception as e:
            logger.error(f"  [ERROR] Failed to migrate {table_name}: {e}")
            self.postgres_session.rollback()
            return False
    
    def migrate_all_data(self):
        """Migrate all data in dependency order"""
        # Migration order is important due to foreign key constraints
        migration_order = [
            (User, 'Users'),
            (Project, 'Projects'),
            (World, 'Worlds'),
            (Character, 'Characters'),
            (StoryThread, 'StoryThreads'),
            (Story, 'Stories'),
            (ScreenplayScene, 'ScreenplayScenes'),
            (StoryboardImage, 'StoryboardImages'),
            (AnimaticsScene, 'AnimaticScenes')
        ]
        
        logger.info("Starting data migration...")
        logger.info("=" * 60)
        
        for model_class, table_name in migration_order:
            if not self.migrate_table(model_class, table_name):
                logger.error(f"[ERROR] Migration failed at table: {table_name}")
                return False
        
        logger.info("=" * 60)
        logger.info("[SUCCESS] All data migrated successfully!")
        return True
    
    def verify_migration(self):
        """Verify that migration was successful by comparing record counts"""
        logger.info("Verifying migration...")
        
        counts = self.get_table_counts()
        
        logger.info("Migration verification results:")
        logger.info("-" * 40)
        
        all_match = True
        for table in counts['sqlite']:
            sqlite_count = counts['sqlite'][table]
            postgres_count = counts['postgres'][table]
            
            if sqlite_count == postgres_count:
                logger.info(f"  {table}: {sqlite_count} records [MATCH]")
            else:
                logger.warning(f"  {table}: SQLite={sqlite_count}, PostgreSQL={postgres_count} [MISMATCH]")
                all_match = False
        
        if all_match:
            logger.info("[SUCCESS] Migration verification passed!")
        else:
            logger.warning("[WARNING] Some record counts don't match. Review migration logs.")
        
        return all_match
    
    def migrate(self):
        """Main migration process"""
        logger.info("=" * 60)
        logger.info("[START] STARTING DATABASE MIGRATION")
        logger.info("FROM: SQLite (sceneweaver.db)")
        logger.info(f"TO: PostgreSQL ({self.postgres_url})")
        logger.info("=" * 60)
        
        try:
            # Step 1: Connect to both databases
            if not self.connect_to_databases():
                return False
            
            # Step 2: Ensure PostgreSQL tables exist
            if not self.ensure_postgres_tables_exist():
                return False
            
            # Step 3: Show initial counts
            logger.info("Initial database state:")
            initial_counts = self.get_table_counts()
            for table in initial_counts['sqlite']:
                sqlite_count = initial_counts['sqlite'][table]
                postgres_count = initial_counts['postgres'][table]
                logger.info(f"  {table}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
            
            # Step 4: Migrate all data
            if not self.migrate_all_data():
                return False
            
            # Step 5: Verify migration
            self.verify_migration()
            
            logger.info("=" * 60)
            logger.info("[SUCCESS] DATABASE MIGRATION COMPLETED!")
            logger.info("Your SQLite data has been migrated to PostgreSQL.")
            logger.info("You can now use PostgreSQL as your primary database.")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Migration failed: {e}")
            return False
        
        finally:
            # Close connections
            if self.sqlite_session:
                self.sqlite_session.close()
            if self.postgres_session:
                self.postgres_session.close()

def main():
    """Main entry point"""
    migrator = DatabaseMigrator()
    
    if migrator.migrate():
        sys.exit(0)
    else:
        logger.error("[ERROR] Database migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()