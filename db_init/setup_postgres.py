#!/usr/bin/env python3
"""
PostgreSQL Database Setup Helper

This script helps create the PostgreSQL database and user if they don't exist.
Run this before running the main initialization script.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        'password': os.getenv('POSTGRES_PASSWORD', 'admin')
    }

def create_database_and_user():
    """Create PostgreSQL database and user using psql commands"""
    config = get_postgres_config()
    
    logger.info("=" * 60)
    logger.info("POSTGRESQL DATABASE SETUP")
    logger.info("=" * 60)
    
    print(f"""
To set up your PostgreSQL database, please run the following commands
in your PostgreSQL command line (psql) as a superuser (e.g., postgres):

1. Connect to PostgreSQL:
   psql -U postgres

2. Create the database:
   CREATE DATABASE "{config['database']}";

3. Create the user:
   CREATE USER {config['user']} WITH PASSWORD '{config['password']}';

4. Grant privileges:
   GRANT ALL PRIVILEGES ON DATABASE "{config['database']}" TO {config['user']};
   GRANT CREATE, USAGE ON SCHEMA public TO {config['user']};
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {config['user']};
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {config['user']};

5. Connect to the new database and grant schema privileges:
   \\c "{config['database']}"
   GRANT ALL ON SCHEMA public TO {config['user']};

6. Exit psql:
   \\q

Configuration from your .env file:
- Host: {config['host']}
- Port: {config['port']}
- Database: {config['database']}
- User: {config['user']}
- Password: {config['password']}
""")
    
    print("=" * 60)
    print("After running these commands, execute: python initialize_db.py")
    print("=" * 60)

if __name__ == "__main__":
    create_database_and_user()