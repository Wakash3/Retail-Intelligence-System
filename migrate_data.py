import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    try:
        # SQLite connection
        sl_conn = sqlite3.connect('retail_intelligence.db')
        sl_cur = sl_conn.cursor()
        
        # PostgreSQL connection
        pg_conn = psycopg2.connect(os.getenv("DB_URL"))
        pg_cur = pg_conn.cursor()
        
        # Get SQLite metadata
        sl_cur.execute("SELECT * FROM pos_sales LIMIT 1")
        sl_cols = [d[0].lower().replace(' ', '_').replace('gross_sales', 'gross_sales').replace('sales_date', 'sales_date') for d in sl_cur.description]
        print(f"SQLite columns found: {sl_cols}")
        
        # PostgreSQL target columns
        pg_cols = [
            'branch', 'department', 'class', 'sku_code', 'product_name',
            'quantity', 'gross_sales', 'discount', 'sales_after_discount',
            'vat_amount', 'net_sale', 'cost_ex_vat', 'net_contribution',
            'margin_pct', 'markup_pct', 'source_file', 'source_branch',
            'sales_date', 'sales_month', 'sales_year'
        ]
        
        # Find index mapping
        mapping = []
        for p_col in pg_cols:
            if p_col in sl_cols:
                mapping.append(sl_cols.index(p_col))
            else:
                # Some might have slightly different names in SQLite
                # e.g. 'Sku Code' -> 'sku_code' (already handled by replace(' ', '_'))
                print(f"Warning: Could not find column {p_col} in SQLite. Using None.")
                mapping.append(None)
        
        # Get data from SQLite
        print("Reading data from SQLite...")
        sl_cur.execute("SELECT * FROM pos_sales")
        rows = sl_cur.fetchall()
        print(f"Found {len(rows)} rows to migrate.")
        
        insert_query = f"INSERT INTO pos_sales ({', '.join(pg_cols)}) VALUES ({', '.join(['%s']*len(pg_cols))}) ON CONFLICT DO NOTHING"
        
        batch_size = 500
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            
            mapped_batch = []
            for row in batch:
                # Extract columns based on mapping and convert inf/null if needed
                mapped_row = []
                for idx in mapping:
                    val = row[idx] if idx is not None else None
                    if isinstance(val, float) and (val == float('inf') or val == float('-inf')):
                        val = 9999.0 # Cap infinity for Postgres Numeric
                    mapped_row.append(val)
                mapped_batch.append(mapped_row)
            
            pg_cur.executemany(insert_query, mapped_batch)
            pg_conn.commit()
            if (i % 5000) == 0:
                print(f"Migrated {i} / {len(rows)} rows.")
            
        print("Migration complete!")
        
        sl_conn.close()
        pg_conn.close()
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
