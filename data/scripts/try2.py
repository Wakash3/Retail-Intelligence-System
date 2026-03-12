from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import time
import os

driver = webdriver.Chrome()  # Make sure ChromeDriver is in your PATH or same folder
driver.maximize_window()
driver.get("http://nexx.rubiskenya.com:9632")
time.sleep(10)

# --- Login ---
user_name = WebDriverWait(driver, 15).until(
    EC.visibility_of_element_located((By.ID, "exampleInputEmail1"))
)
user_name.clear()
user_name.send_keys("betty")
time.sleep(2)

driver.find_element(By.XPATH, "//button[text()='Next']").click()
time.sleep(2)

password_input = WebDriverWait(driver, 15).until(
    EC.visibility_of_element_located((By.ID, "exampleInputPassword1"))
)
password_input.clear()
password_input.send_keys("2027")
time.sleep(2)

driver.find_element(By.XPATH, "//button[text()='Login']").click()
time.sleep(5)
print("Login clicked once")

# --- Modules dropdown ---
modules_toggle = WebDriverWait(driver, 15).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.nav-link.dropdown-toggle[title='Modules']"))
)
modules_toggle.click()
print("Modules dropdown opened")

# --- Daily Reports ---
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

# --- Left pane navigation ---
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

# --- Navigating inside Profitability report ---
org_hierarchy = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.LINK_TEXT, "Organisation Hierarchy"))
)
org_hierarchy.click()
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
time.sleep(3)

# --- Selecting Department ---
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

# Product classification
level_dropdown = driver.find_elements(By.TAG_NAME, "select")[1]
level_dropdown.click()
time.sleep(0.5)
level_dropdown.send_keys("DEPARTMENT")
level_dropdown.send_keys(Keys.DOWN)
level_dropdown.send_keys(Keys.ENTER)
time.sleep(1)

# From / To Department
from_input = driver.find_element(By.XPATH





