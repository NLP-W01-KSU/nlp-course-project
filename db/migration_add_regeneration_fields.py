import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env variables
load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USERNAME")
DB_PASS = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def add_regeneration_columns():
    """Add regeneration tracking columns to feedback table"""
    print("🔄 Running database migration: adding regeneration columns...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Add is_regenerated_feedback column
            conn.execute(text("""
                ALTER TABLE feedback 
                ADD COLUMN IF NOT EXISTS is_regenerated_feedback BOOLEAN DEFAULT FALSE
            """))
            
            # Add regeneration_count column
            conn.execute(text("""
                ALTER TABLE feedback 
                ADD COLUMN IF NOT EXISTS regeneration_count INTEGER DEFAULT 0
            """))
            
            # Add regeneration_type column
            conn.execute(text("""
                ALTER TABLE feedback 
                ADD COLUMN IF NOT EXISTS regeneration_type VARCHAR
            """))
            
            conn.commit()
            print("✅ Added regeneration tracking columns to feedback table")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    add_regeneration_columns()