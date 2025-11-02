# Database Management

This folder contains scripts to initialize fresh databases and migrate data for SceneWeaver.
**Works with both SQLite and PostgreSQL** based on your `.env` configuration.

## Files

- `__init__.py` - Package initialization
- `initialize.py` - Database initialization logic (supports SQLite + PostgreSQL)
- `migrate.py` - Data migration from SQLite to PostgreSQL
- `setup_postgres.py` - Helper to create PostgreSQL database and user
- `README.md` - This documentation

## Quick Start

### Database Initialization

Initialize a fresh database with all required tables:

```bash
python initialize_db.py
# or
python initialize_db.py --init
```

### Database Migration

Migrate existing data from SQLite to PostgreSQL:

```bash
python initialize_db.py --migrate
```

### Get Help

Show all available options:

```bash
python initialize_db.py --help
```

## Detailed Usage

### For SQLite (Local Development)
1. **Update .env file:**
   ```env
   DATABASE_PROVIDER="local"
   DATABASE_URL="sqlite:///./sceneweaver.db"
   ```

2. **Initialize the database:**
   ```bash
   python initialize_db.py --init
   ```

### For PostgreSQL (Production/Shared Development)
1. **Set up PostgreSQL database and user:**
   ```bash
   python db_init/setup_postgres.py
   ```
   This will show you the SQL commands to run in PostgreSQL.

2. **Update .env file:**
   ```env
   DATABASE_PROVIDER="postgresql"
   DATABASE_URL="postgresql://username:password@localhost:5432/database_name"
   ```

3. **Initialize the database:**
   ```bash
   python initialize_db.py --init
   ```

### Migrating from SQLite to PostgreSQL

If you have existing data in SQLite and want to move to PostgreSQL:

1. **Ensure PostgreSQL is set up** (step 1-2 above)
2. **Keep your SQLite file** (`sceneweaver.db`) in the project root
3. **Run the migration:**
   ```bash
   python initialize_db.py --migrate
   ```
4. **Update your .env** to use PostgreSQL
5. **Restart your application**

## What Gets Created/Migrated

The following tables are handled:
- `Users` - User accounts and authentication
- `Projects` - User projects with owner relationships
- `Worlds` - Project world settings
- `Characters` - Project characters
- `StoryThreads` - Story thread content
- `Stories` - Generated stories
- `ScreenplayScenes` - Screenplay scene content
- `StoryboardImages` - Generated storyboard images
- `AnimaticScenes` - Generated animatic scenes

## Migration Features

### Safe Migration
- **Duplicate Prevention**: Skips records that already exist (by ID)
- **Dependency Order**: Migrates tables in correct order to maintain relationships
- **Transaction Safety**: Uses database transactions with rollback on error
- **Verification**: Compares record counts between databases after migration
- **Detailed Logging**: Shows progress and results for each table

### Migration Process
1. **Connects** to both SQLite and PostgreSQL databases
2. **Ensures** PostgreSQL tables exist (creates if needed)
3. **Migrates** data table by table in dependency order
4. **Verifies** migration by comparing record counts
5. **Reports** detailed results

## Configuration

The scripts automatically detect your database type from the `.env` file:

### SQLite Configuration
```env
DATABASE_PROVIDER="local"
DATABASE_URL="sqlite:///./sceneweaver.db"
```

### PostgreSQL Configuration
```env
DATABASE_PROVIDER="postgresql"
DATABASE_URL="postgresql://sceneweaver_admin:admin@localhost:5432/sceneweaver-mvp-db"
```

## Prerequisites

### For SQLite
- No additional setup required
- Database file will be created automatically

### For PostgreSQL
- PostgreSQL server running
- Database and user created with proper permissions
- Correct connection details in `.env` file

### For Migration
- Both SQLite file (`sceneweaver.db`) and PostgreSQL database accessible
- PostgreSQL properly configured in `.env`

## Command Reference

```bash
# Initialize fresh database (based on .env config)
python initialize_db.py
python initialize_db.py --init

# Migrate data from SQLite to PostgreSQL
python initialize_db.py --migrate

# Show help and usage information
python initialize_db.py --help

# Set up PostgreSQL (shows SQL commands to run)
python db_init/setup_postgres.py
```

## Troubleshooting

### SQLite Issues
- Ensure the application has write permissions in the project directory
- Check that the file path in `DATABASE_URL` is accessible

### PostgreSQL Issues
If initialization fails:
1. Check PostgreSQL is running
2. Verify database and user exist
3. Ensure user has CREATE privileges on the database
4. Check connection details in `.env` file
5. Run `python db_init/setup_postgres.py` for setup help

### Migration Issues
If migration fails:
1. Ensure `sceneweaver.db` exists in project root
2. Verify PostgreSQL connection works
3. Check that PostgreSQL user has INSERT privileges
4. Review migration logs for specific table errors
5. Re-run migration (it skips existing records safely)