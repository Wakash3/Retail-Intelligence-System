from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


import time
import os

# Configuration variables
USERNAME = "joy"
PASSWORD = "5971"
BRANCH_NAME = "Enjoy Emma Brenda Membley"
BASE_URL = "http://nexx.rubiskenya.com:9632"

# List of all 25 departments to process
DEPARTMENTS = [
    "Air Time",
    "Alcoholic Beverages", 
    "Bakery",
    "Bazar",
    "Biscuits",
    "CARCARE",
    "Chips & Snacks",
    "Confectionery",
    "Energy Drinks",
    "Fresh product",
    "FROZEN",
    "Groceries",
    "HOT BEVERAGES",
    "Hygiene and health",
    "Ice Cream",
    "Non alcoholic Beverages",
    "PACKAGING BAGS",
    "PHONE CARE",
    "Press",
    "PROBAKERY",
    "SNACKS (ambiant / Box)",
    "TAVIS ALCOHOLIC BEVERAGES",
    "Tobacco",
    "TOYS",
    "Water"
]

def download_report(department_name):
    """Download report for specific department"""
    try:
        print(f"Downloading report for {department_name}...")
        
        # Look for download/export button (try multiple possible selectors)
        download_selectors = [
            "//button[contains(text(),'Download')]",
            "//button[contains(text(),'Export')]", 
            "//a[contains(text(),'Download')]",
            "//a[contains(text(),'Export')]",
            "//button[contains(@title,'Download')]",
            "//button[contains(@title,'Export')]"
        ]
        
        download_button = None
        for selector in download_selectors:
            try:
                download_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                break
            except:
                continue
                
        if download_button:
            download_button.click()
            print(f"✓ Downloaded report for {department_name}")
            time.sleep(3)  # Wait for download to complete
        else:
            print(f"✗ Download button not found for {department_name}")
            
    except Exception as e:
        print(f"✗ Failed to download {department_name}: {e}")

def clear_current_filter():
    """Clear current filter to prepare for next department"""
    try:
        # Look for clear/remove filter button
        clear_selectors = [
            "//button[contains(text(),'Clear')]",
            "//button[contains(text(),'Remove')]",
            "//button[contains(text(),'Reset')]",
            "//button[contains(@title,'Clear')]",
            "//button[contains(@title,'Remove')]"
        ]
        
        clear_button = None
        for selector in clear_selectors:
            try:
                clear_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                break
            except:
                continue
                
        if clear_button:
            clear_button.click()
            print("Filter cleared for next department")
            time.sleep(1)
        else:
            print("No clear button found, continuing...")
            
    except Exception as e:
        print(f"Could not clear filter: {e}")

driver = webdriver.Chrome()  # Make sure ChromeDriver is in your PATH or same folder
try:
    driver.maximize_window()
    
    print("Waiting 30 seconds to avoid rate limiting...")
    time.sleep(30)
    
    driver.get(BASE_URL)
    time.sleep(15)
    
    # Check if already logged in or need manual intervention
    try:
        # Wait a bit for page to fully load
        WebDriverWait(driver, 10).until(
            lambda d: "NexxRetail" in d.title
        )
        print("Page loaded successfully")
        
        # Check if login form is present
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "exampleInputEmail1"))
            )
            print("Login form detected, proceeding with automated login...")
        except TimeoutException:
            print("Login form not detected. You may already be logged in or need manual intervention.")
            print("Please check the browser window and complete login manually if needed.")
            input("Press Enter after you have completed login manually...")
            
    except TimeoutException:
        print("Page load timeout. Please check the browser window.")
        input("Press Enter to continue...")

    #Locating Loggings
    user_name = WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.ID, "exampleInputEmail1"))
    )
    user_name.clear()
    user_name.send_keys(USERNAME)
    WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='Next']"))
    ).click()

    password_input = WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.ID, "exampleInputPassword1"))
    )
    password_input.clear()
    password_input.send_keys(PASSWORD)
    WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='Login']"))
    ).click()
    WebDriverWait(driver, 5).until(
        lambda d: d.current_url != BASE_URL
    )
    print("Login clicked once")
    print(f"Current URL: {driver.current_url}")
    print(f"Page title: {driver.title}")

    # Step 1: Click the Modules dropdown toggle
    print("Looking for Modules dropdown...")
    modules_dropdown_found = False
    try:
        modules_toggle = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.nav-link.dropdown-toggle[title='Modules']"))
        )
        modules_toggle.click()
        modules_dropdown_found = True
        print("Modules dropdown opened")
        
        # Debug: Find all elements in the dropdown
        print("Debugging dropdown contents...")
        try:
            # Wait a moment for dropdown to populate
            time.sleep(2)
            
            # Find all links in the dropdown
            dropdown_links = driver.find_elements(By.CSS_SELECTOR, ".dropdown-menu a, .dropdown-item, [role='menuitem'] a")
            print(f"Found {len(dropdown_links)} links in dropdown:")
            for i, link in enumerate(dropdown_links[:10]):
                print(f"  {i+1}. Text: '{link.text}', Title: '{link.get_attribute('title')}', Href: '{link.get_attribute('href')}'")
            
            # Find any elements with 'report' or 'daily' text
            report_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Report') or contains(text(), 'Daily') or contains(text(), 'report') or contains(text(), 'daily')]")
            print(f"Found {len(report_elements)} elements with report/daily text:")
            for i, elem in enumerate(report_elements[:5]):
                print(f"  {i+1}. Text: '{elem.text}', Tag: {elem.tag_name}")
                
        except Exception as e:
            print(f"Could not debug dropdown: {e}")

        # Click Daily Reports
        daily_reports = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Daily Reports')]"))
        )
        daily_reports.click()
        print("Daily Reports clicked")
        
    except TimeoutException:
        print("Modules dropdown not found. Debugging page structure...")
        
        # Find all dropdown toggles
        try:
            dropdowns = driver.find_elements(By.CSS_SELECTOR, ".dropdown-toggle")
            print(f"Found {len(dropdowns)} dropdown toggles:")
            for i, dropdown in enumerate(dropdowns[:5]):
                print(f"  {i+1}. Text: '{dropdown.text}', Title: '{dropdown.get_attribute('title')}', Class: '{dropdown.get_attribute('class')}'")
        except:
            print("No dropdown toggles found")
        
        # Find all navigation links
        try:
            nav_links = driver.find_elements(By.CSS_SELECTOR, ".nav-link")
            print(f"Found {len(nav_links)} navigation links:")
            for i, link in enumerate(nav_links[:5]):
                print(f"  {i+1}. Text: '{link.text}', Title: '{link.get_attribute('title')}', Class: '{link.get_attribute('class')}'")
        except:
            print("No navigation links found")
        
        # Find elements with 'report' or 'module' text
        try:
            elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Report') or contains(text(), 'report') or contains(text(), 'Module') or contains(text(), 'module')]")
            print(f"Found {len(elements)} elements with report/module text:")
            for i, elem in enumerate(elements[:5]):
                print(f"  {i+1}. Text: '{elem.text}', Tag: {elem.tag_name}")
        except:
            print("Could not find any elements with report/module text")
        
        # Take screenshot to see what the page actually looks like
        try:
            driver.save_screenshot("debug_no_navigation.png")
            print("Screenshot saved as debug_no_navigation.png")
        except:
            print("Could not save screenshot")
        
        print("Cannot proceed without navigation access. Backend restrictions may be active.")
        print("Please try again later or contact the website administrator.")

    if not modules_dropdown_found:
        print("Exiting due to navigation failure.")
        raise Exception("Navigation access blocked - cannot proceed with automation")

    # Wait for either Daily Reports content OR Not Authorized message
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@title='Other Module Reports']"))
        )
        print("Daily Reports page loaded")
    except TimeoutException:
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Not Authorized')]"))
            )
            print("Redirected to Not Authorized page")
        except TimeoutException:
            print("Neither Daily Reports nor Not Authorized detected")

    # Step 3: Use left lane links
    other_module_reports = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@title='Other Module Reports']"))
    )
    other_module_reports.click()
    print("Other Module Reports clicked")

    stock_reports = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@title='Stock Related Reports']"))
    )
    stock_reports.click()
    print("Stock Related Reports clicked")

    profitability_reports = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@title='Profitability']"))
    )
    profitability_reports.click()
    print("Profitability Reports clicked")

    #Navigating to the profitability report
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Organisation Hierarchy"))
    ).click()

    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Organisation Hierarchy"))
    ).click()
    
    # Select organization (first one from dropdown)
    print("Selecting organization...")
    try:
        org_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@role='combobox']"))
        )
        driver.execute_script("arguments[0].click();", org_dropdown)
        
        # Wait for options to appear and select the first one
        time.sleep(2)
        first_option = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='option'][1]"))
        )
        driver.execute_script("arguments[0].click();", first_option)
        print("Selected first organization from dropdown")
        
    except Exception as e:
        print(f"Could not select organization: {e}")
        print("Continuing with department setup...")
    
    # Now proceed with department classification
    print("Setting up department classification...")
    
    # Click Classification link to reveal department filter inputs
    try:
        classification_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Classification')]"))
        )
        classification_link.click()
        print("Clicked Classification link - department filters should now be visible")
        time.sleep(2)  # Wait for filter inputs to appear
    except Exception as e:
        print(f"Could not click Classification link: {e}")
    
    # First, select organization from dropdown, then add as filter
    print("Selecting organization from dropdown...")
    try:
        # Look for organization dropdown
        org_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@role='combobox']"))
        )
        driver.execute_script("arguments[0].click();", org_dropdown)
        
        # Wait for options to appear and select the first one
        time.sleep(2)
        first_option = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='option'][1]"))
        )
        driver.execute_script("arguments[0].click();", first_option)
        print("Selected first organization from dropdown")
        
        # Now add this organization as a filter
        print("Adding selected organization as filter...")
        add_filter_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Add Filter')]"))
        )
        driver.execute_script("arguments[0].click();", add_filter_btn)
        print("Organization filter added successfully")
        time.sleep(2)  # Wait for filter to be applied
        
    except Exception as e:
        print(f"Could not select and add organization filter: {e}")
    
    # Process each department individually (testing with just first department)
    for i, department in enumerate(DEPARTMENTS[:1], 1):  # Only process first department for testing
        print(f"\n=== Processing Department {i}/1: {department} ===")
        
        try:
            # Add department as filter
            print(f"Adding {department} as filter...")
            
            # Look for department input and add department
            dept_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@role='combobox']"))
            )
            driver.execute_script("arguments[0].click();", dept_input)
            dept_input.send_keys(department)
            
            # Select department from dropdown
            dept_option = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, f"//div[@role='option']//span[contains(text(), '{department}')]"))
            )
            driver.execute_script("arguments[0].click();", dept_option)
            print(f"{department} added as filter")
            
            # Add the department filter
            add_filter_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Add Filter')]"))
            )
            driver.execute_script("arguments[0].click();", add_filter_btn)
            print(f"Filter applied for {department}")
            
            # Wait for report to load (no download yet)
            time.sleep(5)
            
            # TODO: Download functionality will be added later
            print(f"Filter setup complete for {department} - download will be added later")
            
            # Clear department filter for next department
            clear_current_filter()
            
            # Small delay between departments
            time.sleep(2)
            
        except Exception as e:
            print(f"Error processing {department}: {e}")
            continue
        
    # Now add Date filter
    print("\n=== Adding Date Filter ===")
    try:
        # Click Date link
        date_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Date')]"))
        )
        date_link.click()
        print("Clicked Date link - date filter options should now be visible")
        time.sleep(2)
        
        # Select Operation = Between
        operation_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@role='combobox']"))
        )
        driver.execute_script("arguments[0].click();", operation_input)
        operation_input.send_keys("Between")
        
        between_option = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='option']//span[text()='Between']"))
        )
        driver.execute_script("arguments[0].click();", between_option)
        print("Date operation set to 'Between'")
        
        # Set From Date (today's date for daily reports)
        from_date_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "field1"))
        )
        from_date_input.clear()
        from_date_input.send_keys("01/03/2026")  # Format: DD/MM/YYYY
        print("From date set")
        
        # Set To Date (today's date for daily reports)
        to_date_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "field2"))
        )
        to_date_input.clear()
        to_date_input.send_keys("01/03/2026")  # Format: DD/MM/YYYY
        print("To date set")
        
        # Add Date filter
        add_filter_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Add Filter')]"))
        )
        driver.execute_script("arguments[0].click();", add_filter_btn)
        print("Date filter added successfully")
        time.sleep(2)
        
    except Exception as e:
        print(f"Could not add date filter: {e}")
    
    # Now add Summary Type filter
    print("\n=== Adding Summary Type Filter ===")
    try:
        # Click Summary link
        summary_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Summary')]"))
        )
        summary_link.click()
        print("Clicked Summary link - summary type options should now be visible")
        time.sleep(2)
        
        # Select False radio button
        false_radio = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//label[contains(text(),'False')]//input[@type='radio']"))
        )
        driver.execute_script("arguments[0].click();", false_radio)
        print("Summary type set to 'False'")
        
        # Add Summary Type filter
        add_filter_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Add Filter')]"))
        )
        driver.execute_script("arguments[0].click();", add_filter_btn)
        print("Summary Type filter added successfully")
        time.sleep(2)
        
    except Exception as e:
        print(f"Could not add summary type filter: {e}")
    
    # Now download the Excel report
    print("\n=== Downloading Excel Report ===")
    try:
        # Wait for report to load with all filters
        time.sleep(5)
        
        # Click Download Excel button
        download_excel_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'DownLoad Excel')]"))
        )
        driver.execute_script("arguments[0].click();", download_excel_btn)
        print("Excel download initiated successfully!")
        
        # Wait for download to complete
        time.sleep(10)  # Extended wait for download
        print("Download completed!")
        
        # Reset all filters
        print("\n=== Resetting All Filters ===")
        try:
            reset_filter_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Reset Filter')]"))
            )
            driver.execute_script("arguments[0].click();", reset_filter_btn)
            print("All filters reset successfully!")
            time.sleep(2)  # Wait for reset to complete
        except Exception as e:
            print(f"Could not reset filters: {e}")
        
    except Exception as e:
        print(f"Could not download Excel report: {e}")
            
    print(f"\n=== Completed processing all {len(DEPARTMENTS[:1])} departments ===")
    print("All filters setup and download completed successfully!")
    print("Automation workflow finished!")

except Exception as e:
    print(f"Script failed with error: {str(e)}")
    raise
finally:
    print("Cleaning up browser...")
    driver.quit()
    print("Browser closed.")


