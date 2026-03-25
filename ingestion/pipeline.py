import sys, traceback
import os

from cleaner.normalise   import clean_all
from cleaner.validator   import validate
from loader.db_loader    import load_to_db

RAW_FOLDER = "data/raw"
CLEAN_FOLDER = "data/clean"

def run_pipeline():
    print('=' * 50)
    # Checks raw files
    if not os.listdir(RAW_FOLDER):
        print("No raw files found. Extraction would normally run here.")
        # run_extraction()  
    else:
        print("STEP 1/3  Raw files already available. Skipping extraction...")

    #  Clean & normalise
    print("STEP 2/3  Cleaning and normalising...")
    df = clean_all(RAW_FOLDER, CLEAN_FOLDER)

    print("Branches found in dataset:")
    print(df['branch'].unique())

    print("\nRows per branch:")
    print(df['branch'].value_counts())

    #  Validate
    print("Validating data quality...")
    validate(df)

    # Load to DB
    print("STEP 3/3  Loading to database...")
    load_to_db(df)

    print("Pipeline completed successfully!")
    print('=' * 50)

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        print(f"PIPELINE FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)