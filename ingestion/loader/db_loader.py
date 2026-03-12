import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
 
load_dotenv()
 
def load_to_db(df):
    engine = create_engine(os.getenv('DB_URL'))
 
    # Load incrementally — append new rows, skip duplicates
    df.to_sql(
        name='pos_sales',
        con=engine,
        if_exists='append',   # Change to 'replace' to reload all data
        index=False,
        method='multi',
        chunksize=500
    )
    print(f'Loaded {len(df)} rows into pos_sales')
