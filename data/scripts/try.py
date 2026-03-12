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
DEPARTMENT = "Water"
BASE_URL = "http://nexx.rubiskenya.com:9632"




driver = webdriver.Chrome()  # Make sure ChromeDriver is in your PATH or same folder
try:
    driver.maximize_window()
    
    print("Waiting 30 seconds to avoid rate limiting...")
    time.sleep(30)
    
    driver.get(BASE_URL)
    time.sleep(15)
    
    # Clear all data after page load to avoid rate limiting
    try:
        driver.delete_all_cookies()
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        print("Browser data cleared successfully")
    except Exception as e:
        print(f"Could not clear some browser data: {e}")
    
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
    try:
        modules_toggle = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.nav-link.dropdown-toggle[title='Modules']"))
        )
        modules_toggle.click()
        print("Modules dropdown opened")
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
        
        raise Exception("Modules dropdown not found - page structure may have changed")

    # Click Daily Reports
    daily_reports = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@title='Daily Reports']"))
    )
    daily_reports.click()
    print("Daily Reports clicked")

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
     

    org_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Branch']"))
    )
    org_input.clear()
    org_input.send_keys(BRANCH_NAME)
    org_input.send_keys(Keys.DOWN)
    org_input.send_keys(Keys.ENTER)

    WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='Add Filter']"))
    ).click()

    #Selecting Department
    WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "classification"))
    ).click()

    #Classification operation
    selects = driver.find_elements(By.TAG_NAME, "select")
    if len(selects) < 2:
        raise Exception("Not enough select elements found")
    
    operation_dropdown = selects[0]
    operation_dropdown.click()
    WebDriverWait(driver, 2).until(
        EC.visibility_of(operation_dropdown)
    )
    operation_dropdown.send_keys("Between")
    operation_dropdown.send_keys(Keys.DOWN)
    operation_dropdown.send_keys(Keys.ENTER)

    #product classification
    level_dropdown = selects[1]
    level_dropdown.click()
    WebDriverWait(driver, 2).until(
        EC.visibility_of(level_dropdown)
    )
    level_dropdown.send_keys("DEPARTMENT")
    level_dropdown.send_keys(Keys.DOWN)
    level_dropdown.send_keys(Keys.ENTER)
    
    #From to Department
    from_input = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='From Value']"))
    )
    from_input.send_keys(DEPARTMENT)
    from_input.send_keys(Keys.DOWN)
    from_input.send_keys(Keys.ENTER)

    to_input = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='To Value']"))
    )
    to_input.send_keys(DEPARTMENT)
    to_input.send_keys(Keys.DOWN)
    to_input.send_keys(Keys.ENTER)

    WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='Add Filter']"))
    ).click()

    print("Script completed successfully!")
    print("Filters applied successfully. You can now extract data from the report.")

except Exception as e:
    print(f"Script failed with error: {str(e)}")
    raise
finally:
    print("Cleaning up browser...")
    driver.quit()
    print("Browser closed.")


