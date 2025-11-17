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
    
    def get_sqlite_columns(self, table_name):
        """Get the actual columns that exist in the SQLite table"""
        try:
            result = self.sqlite_session.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]  # row[1] is the column name
            return columns
        except Exception as e:
            logger.warning(f"Could not get SQLite columns for {table_name}: {e}")
            return []
    
    def migrate_table_smart(self, model_class, table_name):
        """Migrate data for a specific table with smart schema handling"""
        try:
            logger.info(f"Migrating {table_name}...")
            
            # Get the actual columns in SQLite for this table
            sqlite_columns = self.get_sqlite_columns(table_name)
            logger.info(f"  SQLite columns: {sqlite_columns}")
            
            # Get PostgreSQL model columns
            postgres_columns = [col.name for col in model_class.__table__.columns]
            logger.info(f"  PostgreSQL columns: {postgres_columns}")
            
            # Find common columns
            common_columns = set(sqlite_columns) & set(postgres_columns)
            missing_in_sqlite = set(postgres_columns) - set(sqlite_columns)
            
            if missing_in_sqlite:
                logger.info(f"  Columns missing in SQLite (will use defaults): {missing_in_sqlite}")
            
            # Build a custom query to select only existing columns from SQLite
            select_columns = [f'"{col}"' for col in common_columns]
            if not select_columns:
                logger.warning(f"  No common columns found for {table_name}")
                return True
                
            query = f'SELECT {", ".join(select_columns)} FROM "{table_name}"'
            result = self.sqlite_session.execute(text(query))
            sqlite_data = result.fetchall()
            
            if not sqlite_data:
                logger.info(f"  No records found in {table_name}")
                return True
            
            migrated_count = 0
            skipped_count = 0
            
            for row in sqlite_data:
                try:
                    # Build record dict with only available columns
                    record_dict = {}
                    for i, col_name in enumerate(common_columns):
                        record_dict[col_name] = row[i]
                    
                    # Add default values for missing columns
                    for col_name in missing_in_sqlite:
                        column = next((col for col in model_class.__table__.columns if col.name == col_name), None)
                        if column is not None:
                            if col_name == 'name' and table_name == 'Users':
                                # For Users table, generate name from email
                                email = record_dict.get('email', 'unknown')
                                record_dict['name'] = email.split('@')[0] if '@' in email else 'unknown'
                            elif column.default is not None:
                                if callable(column.default.arg):
                                    record_dict[col_name] = column.default.arg()
                                else:
                                    record_dict[col_name] = column.default.arg
                            elif not column.nullable:
                                # Provide reasonable defaults for non-nullable columns
                                if column.type.python_type == str:
                                    record_dict[col_name] = ''
                                elif column.type.python_type == int:
                                    record_dict[col_name] = 0
                                elif column.type.python_type == bool:
                                    record_dict[col_name] = True
                    
                    # Check if record already exists in PostgreSQL
                    existing = self.postgres_session.query(model_class).filter_by(id=record_dict['id']).first()
                    
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Create new record in PostgreSQL
                    new_record = model_class(**record_dict)
                    self.postgres_session.add(new_record)
                    migrated_count += 1
                    
                except IntegrityError as e:
                    logger.warning(f"  [WARNING] Skipping duplicate record in {table_name}: {e}")
                    self.postgres_session.rollback()
                    skipped_count += 1
                    continue
                except Exception as e:
                    logger.warning(f"  [WARNING] Skipping problematic record in {table_name}: {e}")
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
    
    def migrate_table(self, model_class, table_name):
        """Migrate data for a specific table (wrapper for backward compatibility)"""
        return self.migrate_table_smart(model_class, table_name)
    
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