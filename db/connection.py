import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Load .env variables
load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USERNAME")
DB_PASS = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a configured session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Yields a database session (use with 'with' statement or try/finally)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database and create all tables only if they don't exist"""
    try:
        # Import Base from models (where your models are actually defined)
        from db.models import Base
        
        # Test database connection first
        with engine.connect() as conn:
            print("✅ Database connection successful")
        
        # Check if tables already exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        required_tables = ['users', 'content_history', 'feedback']
        
        # Check which tables are missing
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"🔄 Creating {len(missing_tables)} missing table(s): {missing_tables}")
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created successfully")
        else:
            print("✅ All database tables already exist")
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("Please check your:")
        print("  - PostgreSQL server is running")
        print("  - Database exists")
        print("  - .env file has correct credentials")
        raise