from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

#Opening the browser
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Edge(options=options)  # attach only
driver.maximize_window()
time.sleep(2)

#Locating Loggings
"""
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
"""

module_button = WebDriverWait(driver, 15).until(
    EC.element_to_be_clickable((By.CLASS_NAME, "sizeforsmalldevice"))
)
module_button.click()

daily_reports = WebDriverWait(driver, 15).until(
    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Daily Reports')]"))
)
daily_reports.click()
time.sleep(3)

#Left pane
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

#Navigating to the profitability report
driver.find_element(By.LINK_TEXT, "Organisation Hierarchy").click()
time.sleep(2)  # small pause for dropdown to appear

# Selecting the organisation
org_input = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Branch']"))
)
org_input.clear()
org_input.send_keys("Enjoy Emma Brenda Membley")
time.sleep(1)
org_input.send_keys(Keys.DOWN)
org_input.send_keys(Keys.ENTER)

driver.find_element(By.XPATH, "//button[text()='Add Filter']").click()  # Add filter
time.sleep(3)



#Selecting Department
driver.find_element(By.LINK_TEXT, "classification").click()
time.sleep(1)  

#Classification operation
operation_dropdown = driver.find_elements(By.TAG_NAME, "select")[0]
operation_dropdown.click()
time.sleep(0.5)
operation_dropdown.send_keys("Between")
operation_dropdown.send_keys(Keys.DOWN)
operation_dropdown.send_keys(Keys.ENTER)
time.sleep(1)

#product classification
level_dropdown = driver.find_elements(By.TAG_NAME, "select")[1]
level_dropdown.click()
time.sleep(0.5)
level_dropdown.send_keys("DEPARTMENT")
level_dropdown.send_keys(Keys.DOWN)
level_dropdown.send_keys(Keys.ENTER)
time.sleep(1)

#From to Department
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

driver.find_element(By.XPATH, "//button[text()='Add Filter']").click() #Add filter
time.sleep(2)