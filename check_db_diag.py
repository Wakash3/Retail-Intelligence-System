
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def check_db():
    db_url = os.getenv("DB_URL")
    if not db_url:
        print("DB_URL not found in .env")
        return

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Check for tables
            print("--- Tables ---")
            tables = conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'")).fetchall()
            for t in tables:
                print(f"Table: {t[0]}")
            
            # Check for views
            print("\n--- Views ---")
            views = conn.execute(text("SELECT viewname FROM pg_catalog.pg_views WHERE schemaname = 'public'")).fetchall()
            for v in views:
                print(f"View: {v[0]}")
                
            # Check if pos_sales has data
            count = conn.execute(text("SELECT COUNT(*) FROM pos_sales")).scalar()
            print(f"\npos_sales count: {count}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
