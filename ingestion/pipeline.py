import sys, traceback
from extractor.scraper   import run_extraction
from cleaner.normalise   import clean_all
from cleaner.validator   import validate
from loader.db_loader    import load_to_db
 
def run_pipeline():
    print('=' * 50)
    print('STEP 1/3  Extracting data from POS...')
    run_extraction()                    # Selenium scraper — downloads XLSX files
 
    print('STEP 2/3  Cleaning and normalising...')
    df = clean_all('data/raw', 'data/clean')
 
    print('Validating data quality...')
    validate(df)                        # Raises exception if critical issues found
 
    print('STEP 3/3  Loading to database...')
    load_to_db(df)
 
    print('Pipeline completed successfully!')
    print('=' * 50)
 
if __name__ == '__main__':
    try:
        run_pipeline()
    except Exception as e:
        print(f'PIPELINE FAILED: {e}')
        traceback.print_exc()
        sys.exit(1)  # Non-zero exit triggers CI/CD failure alert
