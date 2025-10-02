import os
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
else:
    # Default to SQLite with check_same_thread=False
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
    print("🗄️ Using database provider: local (SQLite)")
    print("🗄️ Initialized SQLite database")
    print("✅ 🗄️ SQLite database connected successfully")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()