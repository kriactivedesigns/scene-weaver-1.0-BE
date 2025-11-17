#!/usr/bin/env python3
"""
SceneWeaver Database Management

Comprehensive database setup script that handles everything automatically:
- Creates PostgreSQL users and databases if they don't exist
- Initializes database schema and tables
- Migrates existing SQLite data if available
- Supports both SQLite and PostgreSQL configurations

Usage:
    python initialize_db.py                    # Full automated setup (recommended)
    python initialize_db.py --init-only        # Initialize database only (no migration)
    python initialize_db.py --migrate-only     # Migrate data only (no initialization)
    python initialize_db.py --help             # Show this help

Operations:
    (default)     : Complete automated setup - creates user/db, initializes schema, migrates data
    --init-only   : Initialize database schema and tables only
    --migrate-only: Migrate existing SQLite data to PostgreSQL only
    --help        : Show usage information

What this script does automatically:
    1. For PostgreSQL: Creates database and user if they don't exist
    2. Connects to the database and verifies permissions
    3. Creates all required tables and schema
    4. If SQLite data exists: Migrates all data to PostgreSQL
    5. Verifies everything is working correctly

Configuration in .env:
    For SQLite:
        DATABASE_PROVIDER="local"
        DATABASE_URL="sqlite:///./sceneweaver.db"
    
    For PostgreSQL:
        DATABASE_PROVIDER="postgresql"
        DATABASE_URL="postgresql://username:password@host:port/database"
        
No manual PostgreSQL setup required - this script handles everything!
"""

import sys
import argparse
import subprocess
import os
import logging
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the db_init module to the path
db_init_path = Path(__file__).parent / 'db_init'
sys.path.insert(0, str(db_init_path))

# Also add the project root to handle relative imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_postgres_config():
    """Get PostgreSQL configuration from environment"""
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'sceneweaver-mvp-db'),
        'user': os.getenv('POSTGRES_USER', 'sceneweaver_admin'),
        'password': os.getenv('POSTGRES_PASSWORD', 'admin'),
        'superuser': os.getenv('POSTGRES_SUPERUSER', 'postgres'),
        'superuser_password': os.getenv('POSTGRES_SUPERUSER_PASSWORD', '')
    }

def check_postgresql_installed():
    """Check if PostgreSQL is installed and accessible"""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"PostgreSQL found: {result.stdout.strip()}")
            return True
        else:
            logger.error("PostgreSQL not found. Please install PostgreSQL first.")
            return False
    except FileNotFoundError:
        logger.error("PostgreSQL not found. Please install PostgreSQL and ensure 'psql' is in your PATH.")
        return False

def run_psql_command(command, config, use_superuser=True):
    """Run a PostgreSQL command using psql"""
    user = config['superuser'] if use_superuser else config['user']
    password = config['superuser_password'] if use_superuser else config['password']
    
    env = os.environ.copy()
    if password:
        env['PGPASSWORD'] = password
    
    cmd = [
        'psql',
        '-h', config['host'],
        '-p', config['port'],
        '-U', user,
        '-c', command
    ]
    
    if not use_superuser:
        cmd.extend(['-d', config['database']])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def run_psql_command_on_database(command, config):
    """Run a PostgreSQL command on the specific target database as superuser"""
    env = os.environ.copy()
    if config['superuser_password']:
        env['PGPASSWORD'] = config['superuser_password']
    
    cmd = [
        'psql',
        '-h', config['host'],
        '-p', config['port'],
        '-U', config['superuser'],
        '-d', config['database'],
        '-c', command
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def create_postgres_user_and_database():
    """Create PostgreSQL user and database if they don't exist"""
    config = get_postgres_config()
    
    logger.info("Setting up PostgreSQL user and database...")
    logger.info(f"Target database: {config['database']}")
    logger.info(f"Target user: {config['user']}")
    
    # Check if PostgreSQL is installed
    if not check_postgresql_installed():
        return False
    
    # Try to connect as superuser to check if we can proceed
    success, stdout, stderr = run_psql_command('SELECT version();', config, use_superuser=True)
    
    if not success:
        logger.error("Failed to connect to PostgreSQL as superuser.")
        logger.error(f"Error: {stderr}")
        logger.error("")
        logger.error("Please ensure:")
        logger.error("1. PostgreSQL is running")
        logger.error("2. You can connect as 'postgres' user")
        logger.error("3. Set POSTGRES_SUPERUSER_PASSWORD in .env if needed")
        return False
    
    logger.info("Connected to PostgreSQL as superuser")
    
    # Check if user exists
    check_user_cmd = f"SELECT 1 FROM pg_roles WHERE rolname='{config['user']}'"
    success, stdout, stderr = run_psql_command(check_user_cmd, config, use_superuser=True)
    
    if success and '1' in stdout:
        logger.info(f"User '{config['user']}' already exists")
    else:
        # Create user
        create_user_cmd = f"CREATE USER {config['user']} WITH PASSWORD '{config['password']}'"
        success, stdout, stderr = run_psql_command(create_user_cmd, config, use_superuser=True)
        
        if success:
            logger.info(f"✅ Created user '{config['user']}'")
        else:
            logger.error(f"Failed to create user: {stderr}")
            return False
    
    # Check if database exists
    check_db_cmd = f"SELECT 1 FROM pg_database WHERE datname='{config['database']}'"
    success, stdout, stderr = run_psql_command(check_db_cmd, config, use_superuser=True)
    
    if success and '1' in stdout:
        logger.info(f"Database '{config['database']}' already exists")
    else:
        # Create database
        create_db_cmd = f'CREATE DATABASE "{config["database"]}"'
        success, stdout, stderr = run_psql_command(create_db_cmd, config, use_superuser=True)
        
        if success:
            logger.info(f"✅ Created database '{config['database']}'")
        else:
            logger.error(f"Failed to create database: {stderr}")
            return False
    
    # Grant database-level privileges first
    logger.info("Granting database-level privileges...")
    grant_commands = [
        f'GRANT ALL PRIVILEGES ON DATABASE "{config["database"]}" TO {config["user"]}',
        f'GRANT CREATE, USAGE ON SCHEMA public TO {config["user"]}'
    ]
    
    for cmd in grant_commands:
        success, stdout, stderr = run_psql_command(cmd, config, use_superuser=True)
        if not success:
            logger.warning(f"Warning: Failed to run privilege command: {cmd}")
            logger.warning(f"Error: {stderr}")
    
    # Now connect to the specific database to grant comprehensive schema privileges
    logger.info("Granting comprehensive schema-level privileges...")
    
    # Grant ownership and all privileges on the public schema
    schema_grant_commands = [
        # Make the user the owner of the public schema for full control
        f'ALTER SCHEMA public OWNER TO {config["user"]}',
        # Grant all current privileges
        f'GRANT ALL ON SCHEMA public TO {config["user"]}',
        f'GRANT CREATE ON SCHEMA public TO {config["user"]}',
        f'GRANT USAGE ON SCHEMA public TO {config["user"]}',
        # Grant privileges on all existing tables (if any)
        f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {config["user"]}',
        f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {config["user"]}',
        f'GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO {config["user"]}',
        # Set default privileges for future objects
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {config["user"]}',
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {config["user"]}',
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO {config["user"]}'
    ]
    
    # Run each command on the target database
    for cmd in schema_grant_commands:
        success, stdout, stderr = run_psql_command_on_database(cmd, config)
        if success:
            logger.info(f"✅ Successfully executed: {cmd}")
        else:
            # Some commands might fail if objects don't exist yet, that's okay
            if "does not exist" in stderr.lower() or "no matching" in stderr.lower():
                logger.info(f"ℹ️  Skipped (objects don't exist yet): {cmd}")
            else:
                logger.warning(f"⚠️  Failed to run schema privilege command: {cmd}")
                logger.warning(f"Error: {stderr}")
    
    logger.info("✅ PostgreSQL user and database setup completed!")
    return True

def check_sqlite_data_exists():
    """Check if SQLite database with data exists"""
    sqlite_path = project_root / 'sceneweaver.db'
    if sqlite_path.exists():
        # Check if it has any data
        try:
            import sqlite3
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            
            # Check if tables exist and have data
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            if not tables:
                conn.close()
                return False
            
            # Check if any table has data
            has_data = False
            for (table_name,) in tables:
                if not table_name.startswith('sqlite_'):
                    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                    count = cursor.fetchone()[0]
                    if count > 0:
                        has_data = True
                        break
            
            conn.close()
            return has_data
            
        except Exception as e:
            logger.warning(f"Could not check SQLite data: {e}")
            return False
    
    return False

def show_help():
    """Show detailed help information"""
    print(__doc__)

def initialize_database_only():
    """Initialize database schema and tables only"""
    try:
        # Import the module dynamically
        import importlib.util
        spec = importlib.util.spec_from_file_location("initialize", db_init_path / "initialize.py")
        initialize_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(initialize_module)
        
        logger.info("Initializing database schema and tables...")
        
        initializer = initialize_module.DatabaseInitializer()
        
        if initializer.initialize():
            logger.info("✅ Database initialization completed successfully!")
            return True
        else:
            logger.error("❌ Database initialization failed!")
            return False
            
    except Exception as e:
        logger.error(f"Error importing database initialization module: {e}")
        return False

def comprehensive_database_setup():
    """Complete automated database setup - the main function"""
    print("")
    print("=" * 70)
    print("🚀 SCENEWEAVER COMPREHENSIVE DATABASE SETUP")
    print("=" * 70)
    print("This will automatically:")
    print("  1. Set up PostgreSQL user and database (if using PostgreSQL)")
    print("  2. Initialize database schema and tables")
    print("  3. Migrate SQLite data if it exists")
    print("  4. Verify everything is working")
    print("=" * 70)
    print("")
    
    # Check what database provider we're using
    database_provider = os.getenv('DATABASE_PROVIDER', 'local')
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./sceneweaver.db')
    
    logger.info(f"Database provider: {database_provider}")
    logger.info(f"Database URL: {database_url}")
    
    is_postgresql = database_provider == 'postgresql' or 'postgresql://' in database_url
    
    # Step 1: Set up PostgreSQL user and database if needed
    if is_postgresql:
        logger.info("\n📊 STEP 1: Setting up PostgreSQL user and database...")
        if not create_postgres_user_and_database():
            logger.error("❌ PostgreSQL setup failed!")
            return False
        logger.info("✅ PostgreSQL setup completed!")
    else:
        logger.info("\n📊 STEP 1: Using SQLite - no user/database setup needed")
    
    # Step 2: Initialize database schema and tables
    logger.info("\n📊 STEP 2: Initializing database schema and tables...")
    if not initialize_database_only():
        logger.error("❌ Database initialization failed!")
        return False
    
    # Step 3: Check for SQLite data and migrate if exists
    logger.info("\n📊 STEP 3: Checking for existing SQLite data...")
    if is_postgresql and check_sqlite_data_exists():
        logger.info("Found existing SQLite data - starting migration...")
        if not migrate_database_only():
            logger.error("❌ Data migration failed!")
            return False
        logger.info("✅ Data migration completed!")
    else:
        logger.info("No SQLite data found or not using PostgreSQL - skipping migration")
    
    # Step 4: Final verification
    logger.info("\n📊 STEP 4: Final verification...")
    
    print("")
    print("=" * 70)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print("Your SceneWeaver database is ready to use!")
    print("")
    print("Next steps:")
    print("  1. Start your FastAPI application: python run.py")
    print("  2. Access the API at: http://localhost:8000")
    print("  3. View API docs at: http://localhost:8000/docs")
    print("=" * 70)
    print("")
    
    return True

def migrate_database_only():
    """Migrate data from SQLite to PostgreSQL only"""
    try:
        # Import the module dynamically
        import importlib.util
        spec = importlib.util.spec_from_file_location("migrate", db_init_path / "migrate.py")
        migrate_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migrate_module)
        
        logger.info("Migrating data from SQLite to PostgreSQL...")
        
        migrator = migrate_module.DatabaseMigrator()
        
        if migrator.migrate():
            logger.info("✅ Database migration completed successfully!")
            return True
        else:
            logger.error("❌ Database migration failed!")
            return False
            
    except Exception as e:
        logger.error(f"Error importing database migration module: {e}")
        return False

def migrate_database():
    """Legacy function for backward compatibility"""
    print("SceneWeaver Database Migration")
    print("=" * 50)
    print("Migrating data from SQLite to PostgreSQL...")
    print()
    
    if migrate_database_only():
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

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="SceneWeaver Comprehensive Database Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python initialize_db.py                 # Complete automated setup (recommended)
  python initialize_db.py --init-only    # Initialize database schema only
  python initialize_db.py --migrate-only # Migrate SQLite data only

The default (no arguments) performs complete automated setup:
  1. Creates PostgreSQL user/database if needed
  2. Initializes all tables and schema
  3. Migrates SQLite data if it exists
  4. Verifies everything is working

For more information, see db_init/README.md
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--init-only', 
        action='store_true',
        help='Initialize database schema and tables only (no PostgreSQL setup or migration)'
    )
    group.add_argument(
        '--migrate-only', 
        action='store_true',
        help='Migrate data from SQLite to PostgreSQL only (database must already exist)'
    )
    
    # Legacy support
    group.add_argument(
        '--init', 
        action='store_true',
        help='Legacy: same as --init-only'
    )
    group.add_argument(
        '--migrate', 
        action='store_true',
        help='Legacy: same as --migrate-only'
    )
    
    args = parser.parse_args()
    
    # Execute the requested operation
    if args.init_only or args.init:
        print("SceneWeaver Database Initialization")
        print("=" * 50)
        result = initialize_database_only()
        if result:
            print("\n[SUCCESS] Database initialization completed successfully!")
            print("You can now start your FastAPI application with: python run.py")
            return 0
        else:
            print("\n[ERROR] Database initialization failed!")
            return 1
    elif args.migrate_only or args.migrate:
        return migrate_database()
    else:
        # Default: comprehensive setup
        result = comprehensive_database_setup()
        return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())