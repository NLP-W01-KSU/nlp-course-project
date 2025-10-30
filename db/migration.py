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

def add_generated_model_column():
    """Add generated_model column to content_history table"""
    print("🔄 Running database migration: adding generated_model column...")
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='content_history' AND column_name='generated_model'
            """))
            
            if result.fetchone() is None:
                print("📝 Adding generated_model column...")
                
                # Add the column
                conn.execute(text("""
                    ALTER TABLE content_history 
                    ADD COLUMN generated_model VARCHAR DEFAULT 'groq'
                """))
                print("✅ Added generated_model column to content_history table")
                
                # Update existing records (set all existing content to groq)
                conn.execute(text("""
                    UPDATE content_history 
                    SET generated_model = 'groq' 
                    WHERE generated_model IS NULL
                """))
                print("✅ Set existing records to 'groq'")
                
                conn.commit()
                print("🎉 Migration completed successfully!")
            else:
                print("✅ generated_model column already exists")
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    add_generated_model_column()