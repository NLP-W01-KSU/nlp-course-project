import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

def get_database_config():
    """Get database configuration from Streamlit secrets or environment variables"""
    try:
        # Try to import streamlit and check secrets (Streamlit Cloud)
        import streamlit as st
        
        # Check if we're in Streamlit and secrets are available
        if hasattr(st, 'secrets') and 'supabase' in st.secrets:
            secrets = st.secrets["supabase"]
            return {
                'user': secrets.get('user'),
                'password': secrets.get('password'),
                'host': secrets.get('host'),
                'port': secrets.get('port', '6543'),  # ⭐ Default to Transaction Pooler port
                'dbname': secrets.get('dbname')
            }
    except (ImportError, AttributeError, KeyError):
        pass  # Not in Streamlit or secrets not available
    
    # Fallback to environment variables (local development)
    from dotenv import load_dotenv
    load_dotenv()
    
    return {
        'user': os.getenv("user"),
        'password': os.getenv("password"),
        'host': os.getenv("host"),
        'port': os.getenv("port", "5432"),  # ⭐ Default to direct port for local
        'dbname': os.getenv("dbname")
    }

# Get database configuration
db_config = get_database_config()

# Validate required configuration
missing_config = [key for key in ['user', 'password', 'host', 'dbname'] if not db_config.get(key)]
if missing_config:
    raise ValueError(f"Missing required database configuration: {missing_config}")

# Construct the SQLAlchemy connection string for Supabase
DATABASE_URL = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}?sslmode=require"

# Create the SQLAlchemy engine with NullPool for serverless environments
engine = create_engine(DATABASE_URL, poolclass=NullPool)  # ⭐ NullPool is CRITICAL for Transaction Pooler

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
            print(f"🔗 Connected to: {db_config['host']}:{db_config['port']}")
        
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
        print("  - Supabase connection details")
        print("  - Environment variables or Streamlit secrets")
        print("  - Database exists in Supabase")
        
        # Don't crash the app in production
        if os.getenv('ENVIRONMENT') == 'development':
            raise

# Optional: Test connection on import
if __name__ == "__main__":
    try:
        with engine.connect() as connection:
            print("✅ Supabase connection test successful!")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")

# import os
# from sqlalchemy import create_engine, inspect
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.pool import NullPool

# def get_database_config():
#     """Get database configuration from Streamlit secrets or environment variables"""
#     try:
#         # Try to import streamlit and check secrets (Streamlit Cloud)
#         import streamlit as st
        
#         # Check if we're in Streamlit and secrets are available
#         if hasattr(st, 'secrets') and 'supabase' in st.secrets:
#             secrets = st.secrets["supabase"]
#             return {
#                 'user': secrets.get('user'),
#                 'password': secrets.get('password'),
#                 'host': secrets.get('host'),
#                 'port': secrets.get('port', '5432'),
#                 'dbname': secrets.get('dbname')
#             }
#     except (ImportError, AttributeError, KeyError):
#         pass  # Not in Streamlit or secrets not available
    
#     # Fallback to environment variables (local development)
#     from dotenv import load_dotenv
#     load_dotenv()
    
#     return {
#         'user': os.getenv("user"),
#         'password': os.getenv("password"),
#         'host': os.getenv("host"),
#         'port': os.getenv("port", "5432"),
#         'dbname': os.getenv("dbname")
#     }

# # Get database configuration
# db_config = get_database_config()

# # Validate required configuration
# missing_config = [key for key in ['user', 'password', 'host', 'dbname'] if not db_config.get(key)]
# if missing_config:
#     raise ValueError(f"Missing required database configuration: {missing_config}")

# # Construct the SQLAlchemy connection string for Supabase
# DATABASE_URL = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}?sslmode=require"

# # Create the SQLAlchemy engine with NullPool for serverless environments
# engine = create_engine(DATABASE_URL, poolclass=NullPool)

# # Create a configured session class
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# def get_db():
#     """Yields a database session (use with 'with' statement or try/finally)"""
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# def init_db():
#     """Initialize database and create all tables only if they don't exist"""
#     try:
#         # Import Base from models (where your models are actually defined)
#         from db.models import Base
        
#         # Test database connection first
#         with engine.connect() as conn:
#             print("✅ Database connection successful")
        
#         # Check if tables already exist
#         inspector = inspect(engine)
#         existing_tables = inspector.get_table_names()
#         required_tables = ['users', 'content_history', 'feedback']
        
#         # Check which tables are missing
#         missing_tables = [table for table in required_tables if table not in existing_tables]
        
#         if missing_tables:
#             print(f"🔄 Creating {len(missing_tables)} missing table(s): {missing_tables}")
#             Base.metadata.create_all(bind=engine)
#             print("✅ Database tables created successfully")
#         else:
#             print("✅ All database tables already exist")
            
#     except Exception as e:
#         print(f"❌ Error initializing database: {e}")
#         print("Please check your:")
#         print("  - Supabase connection details")
#         print("  - Environment variables or Streamlit secrets")
#         print("  - Database exists in Supabase")
        
#         # Don't crash the app in production
#         if os.getenv('ENVIRONMENT') == 'development':
#             raise

# # Optional: Test connection on import
# if __name__ == "__main__":
#     try:
#         with engine.connect() as connection:
#             print("✅ Supabase connection test successful!")
#     except Exception as e:
#         print(f"❌ Failed to connect to Supabase: {e}")