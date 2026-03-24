"""
NexxRetail Selenium Extractor
==============================
Automates the browser to download Profitability Report
for each branch — exactly as you would do it manually.
"""

import os, time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

load_dotenv()

BASE_URL      = "http://nexx.rubiskenya.com:9632"
OUTPUT_FOLDER = os.path.abspath("data/raw")
TARGET_DATE   = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")

ACCOUNTS = [
    {
        "username": os.getenv("NEXX_USERNAME_1", "betty"),
        "password": os.getenv("NEXX_PASSWORD_1", "2027"),
        "branches": ["ENJOY EMMA BRENDA MEMBLEY", "ENJOY EMMA BRENDA 1", "ENJOY EMMA BRENDA 2"],
        "branch_names": ["Membley", "Thome", "Kimbo"],
    },
    {
        "username": os.getenv("NEXX_USERNAME_2", "joy"),
        "password": os.getenv("NEXX_PASSWORD_2", "5971"),
        "branches": ["ENJOY EMMA BRENDA JOGOO RD", "ENJOY EMMA BRENDA TIGONI"],
        "branch_names": ["Jogoo Road", "Tigoni"],
    }
]

def wait(driver, by, value, timeout=15):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )

def make_driver(download_folder):
    os.makedirs(download_folder, exist_ok=True)
    opts = Options()
    opts.add_experimental_option("prefs", {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    })
    opts.add_argument("--start-maximized")
    return webdriver.Chrome(options=opts)

def login(driver, username, password):
    print(f"  Logging in as {username}...")
    driver.get(BASE_URL)
    time.sleep(3)

    user_input = wait(driver, By.ID, "exampleInputEmail1")
    user_input.clear()
    user_input.send_keys(username)
    wait(driver, By.XPATH, "//button[text()='Next']").click()
    time.sleep(1)

    pass_input = wait(driver, By.ID, "exampleInputPassword1")
    pass_input.clear()
    pass_input.send_keys(password)
    wait(driver, By.XPATH, "//button[text()='Login']").click()
    time.sleep(4)

    # Navigate directly to Daily Reports module
    driver.get(f"{BASE_URL}/#/nexx/report/dashboard")
    time.sleep(3)
    print(f"  ✓ Logged in")

def go_to_profitability(driver):
    print("  Navigating to Profitability Report...")
    time.sleep(2)

    # Click Other Module Reports in left sidebar
    wait(driver, By.LINK_TEXT, "Other Module Reports").click()
    time.sleep(1)

    # Click Stock Related Reports
    wait(driver, By.LINK_TEXT, "Stock Related Reports").click()
    time.sleep(1)

    # Click Profitability
    wait(driver, By.LINK_TEXT, "Profitability").click()
    time.sleep(2)
    print("  ✓ On Profitability Report page")

def set_filters_and_download(driver, branch_nexx_name, branch_folder, date_str):
    print(f"  Setting filters for {branch_nexx_name}...")

    # Reset filters first
    try:
        reset = driver.find_element(By.XPATH, "//button[contains(text(),'Reset Filter')]")
        reset.click()
        time.sleep(2)
    except Exception:
        pass

    # --- Organisation Hierarchy filter ---
    wait(driver, By.LINK_TEXT, "Organisation Hierarchy").click()
    time.sleep(1)
    org_input = wait(driver, By.XPATH, "//input[@role='combobox']")
    driver.execute_script("arguments[0].click();", org_input)
    time.sleep(1)
    option = wait(driver, By.XPATH, f"//div[@role='option'][contains(.,'{branch_nexx_name}')]")
    driver.execute_script("arguments[0].click();", option)
    time.sleep(1)
    wait(driver, By.XPATH, "//button[contains(text(),'Add Filter')]").click()
    time.sleep(1)
    print(f"    ✓ Organisation filter set")

    # --- Date filter ---
    wait(driver, By.LINK_TEXT, "Date").click()
    time.sleep(1)
    op_input = wait(driver, By.XPATH, "//input[@role='combobox']")
    driver.execute_script("arguments[0].click();", op_input)
    time.sleep(1)
    wait(driver, By.XPATH, "//div[@role='option'][contains(.,'Between')]").click()
    time.sleep(1)
    from_input = driver.find_element(By.ID, "field1")
    from_input.clear()
    from_input.send_keys(date_str)
    to_input = driver.find_element(By.ID, "field2")
    to_input.clear()
    to_input.send_keys(date_str)
    wait(driver, By.XPATH, "//button[contains(text(),'Add Filter')]").click()
    time.sleep(1)
    print(f"    ✓ Date filter set: {date_str}")

    # --- Summary filter ---
    wait(driver, By.LINK_TEXT, "Summary").click()
    time.sleep(1)
    true_radio = wait(driver, By.XPATH, "//label[contains(.,'True')]//input[@type='radio']")
    driver.execute_script("arguments[0].click();", true_radio)
    wait(driver, By.XPATH, "//button[contains(text(),'Add Filter')]").click()
    time.sleep(1)
    print(f"    ✓ Summary filter set: True")

    # --- Sale Type filter ---
    wait(driver, By.LINK_TEXT, "Sale Type").click()
    time.sleep(1)
    sale_input = wait(driver, By.XPATH, "//input[@role='combobox']")
    driver.execute_script("arguments[0].click();", sale_input)
    time.sleep(1)
    wait(driver, By.XPATH, "//div[@role='option'][contains(.,'POS Issues')]").click()
    wait(driver, By.XPATH, "//button[contains(text(),'Add Filter')]").click()
    time.sleep(1)
    print(f"    ✓ Sale Type filter set: POS Issues")

    # --- Download Excel ---
    print(f"    Downloading Excel...")
    os.makedirs(branch_folder, exist_ok=True)
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": branch_folder
    })
    wait(driver, By.XPATH, "//button[contains(text(),'DownLoad Excel') or contains(text(),'Download Excel')]").click()
    time.sleep(8)
    print(f"    ✓ Downloaded to {branch_folder}")

def process_account(account):
    driver = make_driver(OUTPUT_FOLDER)
    try:
        login(driver, account["username"], account["password"])
        go_to_profitability(driver)
        for nexx_name, branch_name in zip(account["branches"], account["branch_names"]):
            print(f"\n  Branch: {branch_name}")
            folder = os.path.join(OUTPUT_FOLDER, branch_name)
            try:
                set_filters_and_download(driver, nexx_name, folder, TARGET_DATE)
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                try:
                    driver.save_screenshot(f"debug_{branch_name}.png")
                    print(f"  Screenshot saved: debug_{branch_name}.png")
                except Exception:
                    pass
    finally:
        driver.quit()

def run_extraction():
    print("=" * 50)
    print("NEXX SELENIUM EXTRACTOR  Starting...")
    print("=" * 50)
    print(f"\n  Target date: {TARGET_DATE}")
    print(f"  Output folder: {OUTPUT_FOLDER}\n")
    for account in ACCOUNTS:
        if not account["password"]:
            print(f"\n  ⚠ Skipping {account['username']} — password not set")
            continue
        print(f"\n{'=' * 50}")
        print(f"  Account: {account['username']}")
        print(f"{'=' * 50}")
        process_account(account)
    print(f"\n{'=' * 50}")
    print("EXTRACTION COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    run_extraction()
