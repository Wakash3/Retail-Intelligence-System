import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DB_URL'))
cur = conn.cursor()

with open('database/analytics_views.sql', 'r') as f:
    sql = f.read()

cur.execute(sql)
conn.commit()
print("✓ All views created successfully")
cur.close()
conn.close()
