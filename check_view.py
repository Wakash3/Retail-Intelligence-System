import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DB_URL')
if not db_url:
    raise Exception("DB_URL not set")

conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("SELECT to_regclass('vw_department_performance');")
exists = cur.fetchone()[0]
print(f"View exists: {exists}")

cur.execute("SELECT COUNT(*) FROM vw_department_performance;")
count = cur.fetchone()[0]
print(f"Row count: {count}")

if count > 0:
    cur.execute("SELECT * FROM vw_department_performance LIMIT 3;")
    rows = cur.fetchall()
    print("Sample rows:")
    for row in rows:
        print(row)
else:
    print("No data in view.")
    cur.execute("SELECT COUNT(*) FROM pos_sales;")
    pos_count = cur.fetchone()[0]
    print(f"pos_sales row count: {pos_count}")

cur.close()
conn.close()
