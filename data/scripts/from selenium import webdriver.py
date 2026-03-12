from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# === Attach to your already-open Chrome browser ===
# Make sure Chrome is already logged in manually
options = webdriver.ChromeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")  # Chrome must be started with --remote-debugging-port=9222
driver = webdriver.Chrome(options=options)
driver.maximize_window()
time.sleep(2)

# === Start script after login ===

# Click on Module button
module_button = WebDriverWait(driver, 15).until(
    EC.element_to_be_clickable((By.CLASS_NAME, "sizeforsmalldevice"))
)
module_button.click()
print("Module clicked")

# Select Daily Reports
daily_reports = WebDriverWait(driver, 15).until(
    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Daily Reports')]"))
)
daily_reports.click()
time.sleep(2)

# Left pane navigation
other_modules_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.LINK_TEXT, "Other Module Reports"))
)
other_modules_button.click()

stock_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.LINK_TEXT, "Stock Related Reports"))
)
stock_button.click()

profitability_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.LINK_TEXT, "Profitability"))
)
profitability_button.click()

# Organisation Hierarchy
driver.find_element(By.LINK_TEXT, "Organisation Hierarchy").click()
time.sleep(1)

org_input = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Branch']"))
)
org_input.clear()
org_input.send_keys("Enjoy Emma Brenda Membley")
time.sleep(1)
org_input.send_keys(Keys.DOWN)
org_input.send_keys(Keys.ENTER)

driver.find_element(By.XPATH, "//button[text()='Add Filter']").click()
time.sleep(2)

# Classification
driver.find_element(By.LINK_TEXT, "classification").click()
time.sleep(1)

# Classification operation
operation_dropdown = driver.find_elements(By.TAG_NAME, "select")[0]
operation_dropdown.click()
time.sleep(0.5)
operation_dropdown.send_keys("Between")
operation_dropdown.send_keys(Keys.DOWN)
operation_dropdown.send_keys(Keys.ENTER)
time.sleep(1)

# Product classification level
level_dropdown = driver.find_elements(By.TAG_NAME, "select")[1]
level_dropdown.click()
time.sleep(0.5)
level_dropdown.send_keys("DEPARTMENT")
level_dropdown.send_keys(Keys.DOWN)
level_dropdown.send_keys(Keys.ENTER)
time.sleep(1)

# From and To values
from_input = driver.find_element(By.XPATH, "//input[@placeholder='From Value']")
from_input.send_keys("Water")
from_input.send_keys(Keys.DOWN)
from_input.send_keys(Keys.ENTER)
time.sleep(1)

to_input = driver.find_element(By.XPATH, "//input[@placeholder='To Value']")
to_input.send_keys("Water")
to_input.send_keys(Keys.DOWN)
to_input.send_keys(Keys.ENTER)
time.sleep(1)

driver.find_element(By.XPATH, "//button[text()='Add Filter']").click()
time.sleep(2)

print("Filters applied successfully")