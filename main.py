import gspread
from google.oauth2.service_account import Credentials
from gspread import Cell
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import os

##### WHAT YOU NEED TO UPDATE #####
folder_path = r"/tmp" #its where your script is and also need to keep it in r"".

#####

# Set up download directory
DOWNLOAD_DIR = os.path.abspath(folder_path)
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Set Chrome options
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.binary_location = os.getenv("GOOGLE_CHROME_BIN", "/usr/bin/google-chrome")

# Spoof user-agent
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
chrome_options.add_argument(f"user-agent={user_agent}")

# Experimental options
prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)

# Use Service() for WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open Redfin link
url = "https://www.redfin.com/county/1647/MO/Jackson-County/filter/property-type=house,max-price=200k,min-beds=2,min-sqft=750-sqft,hoa=0,viewport=39.23710209353751:38.83281595697974:-94.10456377540925:-94.60859637048101"
driver.get(url)

# Wait for elements
wait = WebDriverWait(driver, 20)

try:
    download_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="download-and-save"]')))

    # Apply previous working scroll logic
    driver.execute_script("arguments[0].scrollIntoView();", download_button)
    time.sleep(2)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_UP)
    time.sleep(3)  # Randomized delay
    driver.execute_script("window.scrollBy(0, 500);")

    # Click the button
    ActionChains(driver).move_to_element(download_button).click().perform()
    time.sleep(2)
    print("✅ Download initiated!")
    email_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="emailInput"]')))
    email_field.send_keys("jordonmedina708@gmail.com")
    time.sleep(2)

    # Click Continue after email
    continue_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//button/span[contains(text(), "Continue")]')))
    continue_button.click()
    time.sleep(3)  # Allow password field to load

    # Enter Password
    password_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="passwordInput"]')))
    password_field.send_keys("jm12345!@#$%")
    time.sleep(3)

    # Click Continue after password
    continue_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//button/span[contains(text(), "Continue")]')))
    continue_button.click()

    time.sleep(5)  # Ensure login completes before proceeding
    print("✅ Logged in successfully!")
    download_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="download-and-save"]')))

    # Apply previous working scroll logic
    driver.execute_script("arguments[0].scrollIntoView();", download_button)
    time.sleep(1)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_UP)
    time.sleep(random.uniform(1.5, 3))  # Randomized delay
    driver.execute_script("window.scrollBy(0, 500);")

    # Click the button
    ActionChains(driver).move_to_element(download_button).click().perform()
    time.sleep(3)
    print("✅ Download initiated!")

except Exception as e:
    print("❌ Download button not found:", e)
# Wait for download to complete
time.sleep(10)

# Close browser
driver.quit()
  # Change this to your folder path
new_name = "redfin.csv"  # Desired new name

# List all CSV files in the folder
csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

if csv_files:
    old_path = os.path.join(folder_path, csv_files[0])  # Pick the first CSV file
    new_path = os.path.join(folder_path, new_name)

    os.rename(old_path, new_path)
    print(f"Renamed '{csv_files[0]}' to '{new_name}'")
else:
    print("No CSV files found in the folder.")

# 🎯 Input CSV file path
input_csv = "/tmp/redfin.csv"  # Change to your CSV file name
output_csv = "/tmp/redfin.csv"

# 🔥 Set up Headers (Simulating a real browser)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.redfin.com/"
}

# 📂 Read CSV file
df = pd.read_csv(input_csv)
df = df.drop(index=0)
# ✅ Backup URL column before any modifications
if "URL (SEE https://www.redfin.com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)" in df.columns:
    df["URL_BACKUP"] = df["URL (SEE https://www.redfin.com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)"]

# Ensure there's a column for results
df["avg AVR/sqft"] = None

# 🔄 Loop through each URL
for index, row in df.iterrows():
    url = row.get("URL (SEE https://www.redfin.com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)", "")

    print(f"🔍 Processing {index + 1}/{len(df)}: {url}")

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            nearby_span = soup.find(lambda tag: tag.name == "span" and "Nearby homes similar to" in tag.text)

            if nearby_span:
                text_content = nearby_span.text.strip()
                match = re.search(r"at an average of \$(\d+)", text_content)

                if match:
                    avg_price_sqft = match.group(1)
                    df.at[index, "avg AVR/sqft"] = "$" + avg_price_sqft
                    print(f"✅ Found AVG/sqft: ${avg_price_sqft}")
                else:
                    df.at[index, "avg AVR/sqft"] = "N/A"
                    print("⚠️ Could not extract AVG/sqft.")
            else:
                df.at[index, "avg AVR/sqft"] = "N/A"
                print("⚠️ 'Nearby homes similar' span not found.")
        else:
            df.at[index, "avg AVR/sqft"] = "Request Failed"
            print(f"❌ Request failed with status code: {response.status_code}")
    except Exception as e:
        df.at[index, "avg AVR/sqft"] = f"Error: {str(e)}"
        print(f"❌ Error occurred: {str(e)}")

    # ⏳ Delay to prevent getting banned
    time.sleep(1)

# ✅ Restore URL column in case it was modified
df["URL"] = df["URL_BACKUP"]
df = df.drop(columns=["URL_BACKUP"])  # Remove backup column

# 💾 Save results to a new CSV file
df.to_csv(output_csv, index=False)
print(f"✅ Scraping completed! Results saved to {output_csv}")


# === 🔹 CONFIGURATION ===
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS")
SPREADSHEET_ID = "1lHnsqMM94omtG_WcXhixVPluETrFtZBcRJ-Hpdag5mM"
SHEET_NAME = "redfin_2025-03-01-22-36-12"
CSV_FILE = "/tmp/redfin.csv"

# === 🔹 Authenticate and Access Google Sheets ===
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# === 🔹 Read Google Sheets Data into DataFrame ===
data = sheet.get_all_values()
df_sheet = pd.DataFrame(data[1:], columns=data[0])  # First row as headers

# === 🔹 Read CSV Data into DataFrame ===
df_csv = pd.read_csv(CSV_FILE, dtype=str)

# === 🔹 Remove "HOA/MONTH" Column (if exists) ===
df_csv = df_csv.drop(columns=["HOA/MONTH"], errors="ignore")
df_sheet = df_sheet.drop(columns=["HOA/MONTH"], errors="ignore")

# === 🔹 Reorder CSV Columns to Match Google Sheet ===
csv_columns = list(df_sheet.columns)

# Move "AVG/sqft" to column AB (index 28)
if "AVG/sqft" in csv_columns:
    csv_columns.remove("AVG/sqft")
    csv_columns.insert(28, "AVG/sqft")

# Ensure "OLD PRICE" exists
if "OLD PRICE" not in df_csv.columns:
    df_csv["OLD PRICE"] = ""

# === 🔹 Reorder CSV and Save for Verification ===
df_csv = df_csv.reindex(columns=csv_columns, fill_value="")
df_csv.to_csv("redfin.csv", index=False)

# === 🔹 Reload CSV File to Ensure Changes are Applied ===
df_csv = pd.read_csv("redfin.csv", dtype=str)

# === 🔹 Convert Integer Columns (Except "YEAR BUILT") ===
integer_columns = ["ZIP OR POSTAL CODE", "SQUARE FEET", "LOT SIZE", "DAYS ON MARKET"]
for col in integer_columns:
    if col in df_csv.columns:
        df_csv[col] = pd.to_numeric(df_csv[col], errors="coerce").fillna(0).astype(int).astype(str)

# === 🔹 Keep "YEAR BUILT" Empty If Missing ===
if "YEAR BUILT" in df_csv.columns:
    df_csv["YEAR BUILT"] = df_csv["YEAR BUILT"].apply(
        lambda x: str(int(float(x))) if pd.notna(x) and x.strip() != "" else "")

# === 🔹 Format Dollar Columns ===
dollar_columns = ["PRICE", "$/SQUARE FEET", "AVG/sqft", "OLD PRICE"]
for col in dollar_columns:
    if col in df_csv.columns:
        df_csv[col] = df_csv[col].apply(lambda x: f"${int(float(x)):,}" if str(x).replace('.', '', 1).isdigit() else x)

# === 🔹 Save the Final CSV Before Updating Google Sheets ===
df_csv.to_csv("redfin.csv", index=False)

# === 🔹 Remove Empty Rows & Duplicates (Based on "ADDRESS" and "YEAR BUILT") ===
df_csv = df_csv[df_csv["ADDRESS"].notna() & df_csv["ADDRESS"].str.strip().ne("")]
df_csv = df_csv.drop_duplicates(subset=["ADDRESS", "YEAR BUILT"], keep="first")

df_sheet = df_sheet[df_sheet["ADDRESS"].notna() & df_sheet["ADDRESS"].str.strip().ne("")]
df_sheet = df_sheet.drop_duplicates(subset=["ADDRESS", "YEAR BUILT"], keep="first")

# === 🔹 Convert NaN to Empty Strings ===
df_csv = df_csv.fillna("")
df_sheet = df_sheet.fillna("")

# === 🔹 Google Sheets Updates ===
IGNORE_COLUMNS = set(df_sheet.columns[18:32])  # Ignore columns R to AE
IGNORE_COLUMNS.discard("URL")  # Except URL

# === 🔹 Add Current Date for New Listings in "added date" Column ===
new_entries = df_csv[
    ~df_csv.set_index(["ADDRESS", "YEAR BUILT"]).index.isin(df_sheet.set_index(["ADDRESS", "YEAR BUILT"]).index)
]

if not new_entries.empty:
    print(f"\n🆕 Found {len(new_entries)} new entries. Adding them to Google Sheets...")

    new_entries["added date"] = datetime.now().strftime('%m/%d/%Y')
    new_entries = new_entries[csv_columns]  # Ensure correct column order

    # 🔹 Find the first empty row after the last filled value in column A
    col_a = sheet.col_values(1)
    start_row = next((i + 1 for i, v in enumerate(col_a) if not v.strip()), len(col_a) + 1)

    # 🔹 Determine range to update (e.g., A101:AG120)
    end_row = start_row + len(new_entries) - 1
    end_col_letter = gspread.utils.rowcol_to_a1(1, len(csv_columns)).split("1")[0]  # E.g., "AG"
    cell_range = f"A{start_row}:{end_col_letter}{end_row}"

    values = new_entries.values.tolist()
    sheet.update(cell_range, values, value_input_option="RAW")
    print(f"✅ Added {len(values)} new entries to rows {start_row} to {end_row}.")

# === 🔹 Iterate Over Existing Rows to Update ===
cells_to_update = []
updates_log = []

for sheet_idx, sheet_row in df_sheet.iterrows():
    key_address = sheet_row["ADDRESS"]
    key_year_built = sheet_row["YEAR BUILT"]

    matched_rows = df_csv[(df_csv["ADDRESS"] == key_address) & (df_csv["YEAR BUILT"] == key_year_built)]
    if matched_rows.empty:
        continue

    csv_row = matched_rows.iloc[0]

    for col in csv_columns:
        if col in ["ADDRESS", "YEAR BUILT", "added date"] or col in IGNORE_COLUMNS:
            continue

        sheet_value = str(sheet_row.get(col, "")).strip()
        csv_value = str(csv_row.get(col, "")).strip()

        if sheet_value.lower() == "nan":
            sheet_value = ""
        if csv_value.lower() == "nan":
            csv_value = ""

        if csv_value == "" and sheet_value != "":
            continue

        row_index = sheet_idx + 2
        col_index = csv_columns.index(col) + 1

        if sheet_value != csv_value:
            cells_to_update.append(Cell(row_index, col_index, csv_value))
            updates_log.append(f"Row {row_index}: {col} updated to '{csv_value}' (Old: '{sheet_value}')")

# === 🔹 Apply Updates to Google Sheets ===
if cells_to_update:
    sheet.update_cells(cells_to_update, value_input_option="RAW")
    print("\n🔄 Update Log:")
    for log in updates_log:
        print(log)
    print(f"\n✅ Update complete! {len(cells_to_update)} cells updated.")
else:
    print("✅ No updates needed.")


file = '/tmp/redfin.csv'
if(os.path.exists(file) and os.path.isfile(file)):
  os.remove(file)
  print("file deleted")
else:
  print("file not found")
