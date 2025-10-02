#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes a fresh database with all required tables and columns
for the SceneWeaver application. Works with both SQLite and PostgreSQL based
on DATABASE_PROVIDER and DATABASE_URL in .env file.
"""

import os
import sys
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models import Base
from app.database import DATABASE_URL, DATABASE_PROVIDER
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Handles database initialization for SceneWeaver"""
    
    def __init__(self):
        self.database_url = DATABASE_URL
        self.database_provider = DATABASE_PROVIDER
        self.engine = None
        self.is_sqlite = self.database_provider == "local" or "sqlite" in str(self.database_url).lower()
        
    def connect_to_database(self):
        """Establish connection to the database"""
        try:
            logger.info(f"Database Provider: {self.database_provider}")
            logger.info(f"Database Type: {'SQLite' if self.is_sqlite else 'PostgreSQL'}")
            logger.info(f"Connecting to database...")
            
            if self.is_sqlite:
                # SQLite connection
                self.engine = create_engine(self.database_url, connect_args={"check_same_thread": False})
                # Test connection
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT sqlite_version()"))
                    version = result.fetchone()[0]
                    logger.info(f"[SUCCESS] Connected to SQLite version: {version}")
            else:
                # PostgreSQL connection
                self.engine = create_engine(self.database_url)
                # Test connection
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT version()"))
                    version = result.fetchone()[0]
                    logger.info(f"[SUCCESS] Connected to PostgreSQL: {version}")
                
            return True
            
        except OperationalError as e:
            if "does not exist" in str(e) and not self.is_sqlite:
                logger.error("[ERROR] PostgreSQL database does not exist. Please create the database first:")
                logger.error(f"   CREATE DATABASE {os.getenv('POSTGRES_DB')};")
                logger.error("   Or run: python db_init/setup_postgres.py for full setup instructions")
            else:
                logger.error(f"[ERROR] Connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error connecting to database: {e}")
            return False
    
    def check_database_permissions(self):
        """Check if the database user has necessary permissions"""
        try:
            with self.engine.connect() as conn:
                if self.is_sqlite:
                    # SQLite doesn't have permission issues, just test basic functionality
                    conn.execute(text("SELECT 1"))
                    logger.info("[SUCCESS] SQLite database access verified")
                else:
                    # PostgreSQL - try to create a test table to verify permissions
                    conn.execute(text("CREATE TABLE IF NOT EXISTS _permission_test (id INTEGER)"))
                    conn.execute(text("DROP TABLE _permission_test"))
                    conn.commit()
                    logger.info("[SUCCESS] PostgreSQL database permissions verified")
                return True
        except Exception as e:
            if self.is_sqlite:
                logger.error(f"[ERROR] SQLite database access error: {e}")
            else:
                logger.error(f"[ERROR] Insufficient PostgreSQL permissions: {e}")
                logger.error("Please ensure your database user has CREATE privileges:")
                logger.error(f"   GRANT CREATE, USAGE ON SCHEMA public TO {os.getenv('POSTGRES_USER')};")
            return False
    
    def create_tables(self):
        """Create all database tables"""
        try:
            logger.info("Creating database tables...")
            
            # Create all tables defined in models
            Base.metadata.create_all(bind=self.engine)
            
            # Verify tables were created
            with self.engine.connect() as conn:
                if self.is_sqlite:
                    result = conn.execute(text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                        ORDER BY name
                    """))
                else:
                    result = conn.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """))
                tables = [row[0] for row in result.fetchall()]
                
            logger.info(f"[SUCCESS] Created {len(tables)} tables:")
            for table in tables:
                logger.info(f"   - {table}")
                
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error creating tables: {e}")
            return False
    
    def verify_schema(self):
        """Verify that all expected tables and columns exist"""
        try:
            logger.info("Verifying database schema...")
            
            expected_tables = [
                'Users', 'Projects', 'Worlds', 'Characters', 
                'StoryThreads', 'Stories', 'ScreenplayScenes', 
                'StoryboardImages', 'AnimaticScenes'
            ]
            
            with self.engine.connect() as conn:
                for table in expected_tables:
                    if self.is_sqlite:
                        result = conn.execute(text(f"PRAGMA table_info({table})"))
                        columns = result.fetchall()
                    else:
                        result = conn.execute(text(f"""
                            SELECT column_name, data_type 
                            FROM information_schema.columns 
                            WHERE table_name = '{table}'
                            ORDER BY ordinal_position
                        """))
                        columns = result.fetchall()
                    
                    if columns:
                        logger.info(f"[SUCCESS] Table '{table}' has {len(columns)} columns")
                    else:
                        logger.warning(f"[WARNING] Table '{table}' not found or has no columns")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error verifying schema: {e}")
            return False
    
    def initialize(self):
        """Main initialization process"""
        logger.info("=" * 60)
        logger.info("[START] STARTING DATABASE INITIALIZATION")
        logger.info("=" * 60)
        
        # Step 1: Connect to database
        if not self.connect_to_database():
            return False
            
        # Step 2: Check permissions
        if not self.check_database_permissions():
            return False
            
        # Step 3: Create tables
        if not self.create_tables():
            return False
            
        # Step 4: Verify schema
        if not self.verify_schema():
            return False
            
        logger.info("=" * 60)
        logger.info("[SUCCESS] DATABASE INITIALIZATION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        db_type = "SQLite" if self.is_sqlite else "PostgreSQL"
        logger.info(f"Your {db_type} database is ready for SceneWeaver.")
        logger.info("You can now start your FastAPI application.")
        logger.info("=" * 60)
        
        return True

def main():
    """Main entry point"""
    initializer = DatabaseInitializer()
    
    if initializer.initialize():
        sys.exit(0)
    else:
        logger.error("❌ Database initialization failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()