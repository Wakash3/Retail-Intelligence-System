
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def apply_sql():
    db_url = os.getenv("DB_URL")
    sql_path = r"database\analytics_views.sql"
    
    if not os.path.exists(sql_path):
        print(f"SQL file not found at {sql_path}")
        return

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        with open(sql_path, "r") as f:
            sql = f.read()
            
        print("Applying analytics views...")
        cur.execute(sql)
        print("Success!")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error applying SQL: {e}")

if __name__ == "__main__":
    apply_sql()
