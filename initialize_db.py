#!/usr/bin/env python3
"""
SceneWeaver Database Management

Root-level script to manage database operations for SceneWeaver.
Supports initialization of fresh databases and migration from SQLite to PostgreSQL.

Usage:
    python initialize_db.py                    # Initialize database (based on .env config)
    python initialize_db.py --init             # Initialize database (same as above)
    python initialize_db.py --migrate          # Migrate data from SQLite to PostgreSQL
    python initialize_db.py --help             # Show this help

Operations:
    --init     : Initialize a fresh database with all tables and schema
    --migrate  : Migrate existing data from sceneweaver.db to PostgreSQL
    --help     : Show usage information

Prerequisites:
    For initialization:
        SQLite: No additional setup required
        PostgreSQL: Database and user must exist (see db_init/setup_postgres.py)
    
    For migration:
        PostgreSQL database must be configured in .env
        sceneweaver.db file must exist in project root

Configuration in .env:
    For SQLite:
        DATABASE_PROVIDER="local"
        DATABASE_URL="sqlite:///./sceneweaver.db"
    
    For PostgreSQL:
        DATABASE_PROVIDER="postgresql"
        DATABASE_URL="postgresql://username:password@host:port/database"
"""

import sys
import argparse
from pathlib import Path

# Add the db_init module to the path
db_init_path = Path(__file__).parent / 'db_init'
sys.path.insert(0, str(db_init_path))

# Also add the project root to handle relative imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def show_help():
    """Show detailed help information"""
    print(__doc__)

def initialize_database():
    """Initialize a fresh database"""
    try:
        # Import the module dynamically
        import importlib.util
        spec = importlib.util.spec_from_file_location("initialize", db_init_path / "initialize.py")
        initialize_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(initialize_module)
        
        print("SceneWeaver Database Initialization")
        print("=" * 50)
        
        initializer = initialize_module.DatabaseInitializer()
        
        if initializer.initialize():
            print("\n[SUCCESS] Database initialization completed successfully!")
            print("You can now start your FastAPI application with: python run.py")
            return 0
        else:
            print("\n[ERROR] Database initialization failed!")
            print("Check the logs above for details.")
            print("\nFor PostgreSQL setup help: python db_init/setup_postgres.py")
            print("For SQLite, ensure DATABASE_PROVIDER='local' and DATABASE_URL='sqlite:///./sceneweaver.db'")
            return 1
            
    except Exception as e:
        print(f"[ERROR] Error importing database initialization module: {e}")
        print("Make sure you're running this script from the project root directory.")
        return 1

def migrate_database():
    """Migrate data from SQLite to PostgreSQL"""
    try:
        # Import the module dynamically
        import importlib.util
        spec = importlib.util.spec_from_file_location("migrate", db_init_path / "migrate.py")
        migrate_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migrate_module)
        
        print("SceneWeaver Database Migration")
        print("=" * 50)
        print("Migrating data from SQLite to PostgreSQL...")
        print()
        
        migrator = migrate_module.DatabaseMigrator()
        
        if migrator.migrate():
            print("\n[SUCCESS] Database migration completed successfully!")
            print("Your SQLite data has been migrated to PostgreSQL.")
            print("Update your .env to use PostgreSQL and restart your application.")
            return 0
        else:
            print("\n[ERROR] Database migration failed!")
            print("Check the logs above for details.")
            print("\nEnsure:")
            print("- PostgreSQL is running and accessible")
            print("- sceneweaver.db exists in project root")
            print("- PostgreSQL credentials in .env are correct")
            return 1
            
    except Exception as e:
        print(f"[ERROR] Error importing database migration module: {e}")
        print("Make sure you're running this script from the project root directory.")
        return 1

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="SceneWeaver Database Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python initialize_db.py              # Initialize database
  python initialize_db.py --init       # Initialize database  
  python initialize_db.py --migrate    # Migrate SQLite to PostgreSQL

For more information, see db_init/README.md
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--init', 
        action='store_true',
        help='Initialize a fresh database with tables and schema'
    )
    group.add_argument(
        '--migrate', 
        action='store_true',
        help='Migrate data from SQLite (sceneweaver.db) to PostgreSQL'
    )
    
    args = parser.parse_args()
    
    # Default to initialization if no arguments provided
    if not args.migrate and not args.init:
        args.init = True
    
    # Execute the requested operation
    if args.init:
        return initialize_database()
    elif args.migrate:
        return migrate_database()

if __name__ == "__main__":
    sys.exit(main())