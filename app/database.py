import os
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_PROVIDER = os.getenv("DATABASE_PROVIDER")
DATABASE_URL = os.getenv("DATABASE_URL")

# Handle different database providers
if DATABASE_PROVIDER == "postgresql":
    DATABASE_URL = os.getenv("DATABASE_URL")
    # PostgreSQL doesn't need check_same_thread
    engine = create_engine(DATABASE_URL)
    print("🗄️ Using database provider: postgresql")
    print("🗄️ Initialized PostgreSQL database")
    print("✅ 🗄️ PostgreSQL database connected successfully")
elif DATABASE_PROVIDER == "gcp_postgresql":

    # PostgreSQL on GCP doesn't need check_same_thread
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_name = os.getenv("DB_NAME")
    db_port = os.getenv("DB_PORT")
    unix_socket_path = os.getenv("INSTANCE_UNIX_SOCKET")

    if unix_socket_path:
        # Cloud Run: Use Unix socket
        print("🗄️  Using database provider: GCP Cloud SQL (Unix Socket)")
        db_url = sqlalchemy.engine.url.URL.create(
            drivername="postgresql+pg8000",
            username=db_user,
            password=db_pass,
            database=db_name,
            query={"unix_sock": f"{unix_socket_path}/.s.PGSQL.{db_port}"},
        )
    else: 
        # Local development: Use TCP connection via Cloud SQL Proxy
        print(f"🗄️  Using database provider: GCP Cloud SQL (TCP via Proxy)")

        db_host = os.getenv("DB_HOST")

        print(f"    Connecting to {db_host}:{db_port}")
        db_url = sqlalchemy.engine.url.URL.create(
            drivername="postgresql+pg8000",
            username=db_user,
            password=db_pass,
            host=db_host,
            port=db_port,
            database=db_name,
        )

    print("🗄️ GCP PostgreSQL URL", db_url)

    engine = create_engine(db_url)
    
    print("🗄️ Initialized GCP PostgreSQL database")
    print("✅ 🗄️ GCP PostgreSQL database connected successfully")

elif DATABASE_PROVIDER == "sqlite":
    # Default to SQLite with check_same_thread=False
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
    print("🗄️ Using database provider: local (SQLite)")
    print("🗄️ Initialized SQLite database")
    print("✅ 🗄️ SQLite database connected successfully")
else:
    # If no valid provider is set, raise an error to prevent accidental misconfiguration
    raise ValueError(f"Unsupported or missing DATABASE_PROVIDER: '{DATABASE_PROVIDER}'. Please check your .env file.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()