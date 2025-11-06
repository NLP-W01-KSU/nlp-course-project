import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

def get_database_config():
    """Get database configuration for HuggingFace Spaces AND local development"""
    
    config_sources = []
    
    # 1. HuggingFace Spaces Secrets (Primary for HF)
    hf_config = {
        'user': os.getenv("HF_DB_USER"),
        'password': os.getenv("HF_DB_PASSWORD"),
        'host': os.getenv("HF_DB_HOST"),
        'port': os.getenv("HF_DB_PORT", "6543"),  # Transaction Pooler port
        'dbname': os.getenv("HF_DB_NAME")
    }
    
    if all([hf_config['user'], hf_config['password'], hf_config['host'], hf_config['dbname']]):
        config_sources.append(('HuggingFace Secrets', hf_config))
        print("✅ Found HuggingFace database configuration")
    
    # 2. Streamlit Secrets (For Streamlit Cloud) - FIXED: Better error handling
    try:
        # Only import streamlit if we're actually in Streamlit environment
        import streamlit as st
        if hasattr(st, 'secrets') and st.secrets:
            if 'supabase' in st.secrets:
                secrets = st.secrets["supabase"]
                st_config = {
                    'user': secrets.get('user'),
                    'password': secrets.get('password'),
                    'host': secrets.get('host'),
                    'port': secrets.get('port', '6543'),
                    'dbname': secrets.get('dbname')
                }
                if all(st_config.values()):
                    config_sources.append(('Streamlit Secrets', st_config))
                    print("✅ Found Streamlit database configuration")
    except Exception as e:
        # Silently continue if not in Streamlit environment
        pass
    
    # 3. Local Development Environment Variables
    try:
        from dotenv import load_dotenv
        load_dotenv()  # Load .env file for local development
    except ImportError:
        pass  # dotenv not available
    
    local_config = {
        'user': os.getenv("DB_USER") or os.getenv("user"),
        'password': os.getenv("DB_PASSWORD") or os.getenv("password"),
        'host': os.getenv("DB_HOST") or os.getenv("host"),
        'port': os.getenv("DB_PORT") or os.getenv("port", "6543"),
        'dbname': os.getenv("DB_NAME") or os.getenv("dbname")
    }
    
    if all([local_config['user'], local_config['password'], local_config['host'], local_config['dbname']]):
        config_sources.append(('Local Environment', local_config))
        print("✅ Found local development database configuration")
    
    # Select the best available configuration
    if config_sources:
        source_name, config = config_sources[0]
        print(f"🔗 Using database: {config['host']}:{config['port']} (source: {source_name})")
        return config
    else:
        print("🚫 No database configuration found - running in database-less mode")
        return None

def create_database_engine():
    """Create database engine with proper configuration"""
    db_config = get_database_config()
    
    if not db_config:
        return None
    
    try:
        # Construct connection URL
        DATABASE_URL = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        
        # Add SSL mode for Supabase
        if db_config['host'].endswith('supabase.co'):
            DATABASE_URL += "?sslmode=require"
        
        # Create engine with optimized settings
        engine = create_engine(
            DATABASE_URL,
            poolclass=NullPool,  # Critical for serverless environments
            pool_pre_ping=True,  # Verify connection before use
            echo=False,  # Set to True for SQL debugging
            connect_args={
                'connect_timeout': 10,
                'keepalives': 1,
                'keepalives_idle': 30,
            }
        )
        
        # Test connection
        with engine.connect() as conn:
            print(f"✅ Database connection successful to {db_config['host']}")
        
        return engine
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Running in database-less mode")
        return None

# Create engine instance
engine = create_database_engine()

# Create session maker if engine is available
if engine:
    SessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=engine,
        expire_on_commit=False  # Better for serverless
    )
else:
    SessionLocal = None
    print("⚠️ No database connection - some features will be limited")

def get_db():
    """Yields a database session with fallback for no database"""
    if not SessionLocal:
        # Return mock session for database-less mode
        class MockSession:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def query(self, *args, **kwargs):
                return self
            def filter(self, *args, **kwargs):
                return self
            def all(self):
                return []
            def first(self):
                return None
            def add(self, *args, **kwargs):
                print("⚠️ Mock DB: add() called but no database configured")
            def commit(self):
                print("⚠️ Mock DB: commit() called but no database configured")
            def rollback(self):
                pass
            def delete(self, *args, **kwargs):
                pass
        
        return MockSession()
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"❌ Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database if available"""
    if not engine:
        print("🚫 No database - running in read-only mode")
        return
    
    try:
        from db.models import Base
        
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
        print(f"⚠️ Database initialization note: {e}")

def is_database_available():
    """Check if database is available"""
    return engine is not None

def get_database_status():
    """Get database connection status"""
    if not engine:
        return {"status": "not_configured", "message": "No database configuration"}
    
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT version();")
            version = result.scalar()
            
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            return {
                "status": "connected",
                "tables": len(tables),
                "type": "supabase_transaction_pooler",
                "version": version[:100] + "..." if len(version) > 100 else version
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Initialize database on import with error handling
try:
    init_db()
except Exception as e:
    print(f"⚠️ Database initialization failed: {e}")
    print("💡 App will run in database-less mode")

# Export status
database_status = get_database_status()
print(f"📊 Database Status: {database_status['status']}")

# Optional: Test connection on import
if __name__ == "__main__":
    if engine:
        try:
            with engine.connect() as connection:
                print("✅ Database connection test successful!")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
    else:
        print("🚫 No database configured")