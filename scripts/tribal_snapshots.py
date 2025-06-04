import os
import time
import re
import json
import traceback
import pandas as pd
import tldextract # Ensure this is installed: pip install tldextract
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException

# === CONFIGURATION ===
# Ensure these paths are correct for your system
EXCEL_INPUT = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\scripts\TribalLeadership_Directory_-2947355220576375878.xlsx"
EXCEL_OUTPUT = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\scripts\TribalLeadership_WithScreenshots_AndURLs.xlsx" # <<< MODIFIED: Output Excel name
FAILURE_LOG_PATH = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\scripts\failures.log"
SCREENSHOT_DIR = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\hpsnaps"
JSON_OUTPUT = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\data\tribalDirectory.json"
TIMEOUT = 15  # seconds
MAX_TRIES = 3
RESTART_INTERVAL = 25 # Number of URLs processed before restarting the browser

SKIP_DOMAINS = {
    "google.com", "bing.com", "yahoo.com", "aol.com", "msn.com", "ask.com",
    "icloud.com", "outlook.com", "facebook.com", "instagram.com", "twitter.com"
    # Add other domains to skip if necessary
}

# Create directories if they don't exist
os.makedirs(os.path.dirname(EXCEL_OUTPUT), exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(JSON_OUTPUT), exist_ok=True)

# === EXTRACT URLs FROM EXCEL ===
print(f"🔄 Reading Excel file: {EXCEL_INPUT}")
try:
    excel_data = pd.read_excel(EXCEL_INPUT, sheet_name=None) # Read all sheets
except FileNotFoundError:
    print(f"❌ ERROR: Excel input file not found at {EXCEL_INPUT}. Please check the path.")
    exit()

df_combined = pd.concat(excel_data.values(), ignore_index=True)
original_df = df_combined.copy()
print(f"Found {len(original_df)} rows in the Excel file.")

def extract_urls_from_text(text_content):
    # Regex to find URLs (handles http, https, or no scheme, and www or no www)
    pattern = r'\b(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?'
    return re.findall(pattern, str(text_content))

all_extracted_urls = []
# url_to_row_index maps a normalized URL to the original DataFrame row index
# This is important if a URL could be associated with multiple rows,
# or if you want to ensure each row gets its primary URL.
# For now, we'll map the *first* URL found for a row if multiple exist in that row's cells.
# And if a URL is found in multiple rows, url_to_row will store the index of the *first* row it was found in.
url_to_row_index = {}

print("🔎 Extracting URLs from Excel cells...")
for idx, row in original_df.iterrows():
    urls_in_row = set() # To store unique URLs found in the current row
    for cell_value in row.values:
        for extracted_url in extract_urls_from_text(cell_value):
            # Normalize URL: add http:// if no scheme is present
            normalized_url = 'http://' + extracted_url if not extracted_url.startswith(('http://', 'https://')) else extracted_url
            urls_in_row.add(normalized_url)
            
            # Map the normalized URL to its original row index if not already mapped
            # This prioritizes the first row a unique URL is found in.
            if normalized_url not in url_to_row_index:
                url_to_row_index[normalized_url] = idx
    
    all_extracted_urls.extend(list(urls_in_row)) # Add all unique URLs from this row to the global list

# Deduplicate URLs based on the root domain (e.g., example.com from www.example.com or sub.example.com)
# This list will be used for taking screenshots to avoid multiple screenshots of the same base site.
def get_domain_suffix(url_string):
    try:
        extracted_parts = tldextract.extract(url_string)
        # Only consider domain and suffix for uniqueness check
        return f"{extracted_parts.domain}.{extracted_parts.suffix}".lower()
    except Exception as e:
        print(f"⚠️ Error extracting domain from {url_string}: {e}")
        return None

unique_domains_processed = set()
urls_to_screenshot = [] # This list will hold one URL per unique domain

print("🔍 Filtering URLs to get one per unique domain for screenshots...")
for url_val in all_extracted_urls: # Iterate through all URLs found
    domain_part = get_domain_suffix(url_val)
    if not domain_part: # Skip if domain extraction failed
        continue

    if domain_part in SKIP_DOMAINS:
        print(f"🚫 Skipping common/undesired domain: {url_val} (domain: {domain_part})")
        continue
    
    if domain_part not in unique_domains_processed:
        unique_domains_processed.add(domain_part)
        urls_to_screenshot.append(url_val)

print(f"Found {len(urls_to_screenshot)} unique URLs to attempt screenshots for.")


# === Setup browser ===
def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no browser window)
    chrome_options.add_argument("--window-size=1600,1200") # Define window size for screenshots
    chrome_options.add_argument("--disable-gpu") # Recommended for headless
    chrome_options.add_argument("--no-sandbox") # Can help in some environments
    chrome_options.add_argument("--disable-dev-shm-usage") # Overcomes limited resource problems
    # Standard User-Agent to mimic a real browser
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(TIMEOUT) # Timeout for page loads
        return driver
    except WebDriverException as e:
        print(f"❌ WebDriver Error during initialization: {e}")
        print("Ensure ChromeDriver is in your PATH or accessible by Selenium.")
        exit()

# Stores {original_row_index: "screenshot_filename.png"}
screenshot_filename_records = {}
# <<< ADDED: Stores {original_row_index: "http://actual_url_used_for_screenshot.com"}
successful_url_records = {} 
failed_screenshots = []

def generate_screenshot_filename(url_string):
    try:
        extracted_parts = tldextract.extract(url_string)
        # Create a filename from domain and suffix, sanitizing it
        base_filename = f"{extracted_parts.domain}_{extracted_parts.suffix}"
        sanitized_filename = re.sub(r'[^\w-]', '_', base_filename) # Replace non-alphanumeric (except underscore/hyphen) with underscore
        return f"{sanitized_filename}.png"
    except Exception: # Fallback if tldextract fails for some reason
        return f"screenshot_{int(time.time())}.png"


current_driver = initialize_driver()
print("\n🚀 Starting screenshot process...")

try:
    for i, target_url in enumerate(urls_to_screenshot):
        if i > 0 and i % RESTART_INTERVAL == 0:
            print(f"\n🔄 Restarting browser after {RESTART_INTERVAL} URLs...")
            if current_driver:
                current_driver.quit()
            current_driver = initialize_driver()
            time.sleep(2) # Brief pause after restart

        print(f"\nAttempting ({i+1}/{len(urls_to_screenshot)}): {target_url}")
        screenshot_taken_for_url = False
        for attempt in range(MAX_TRIES):
            try:
                start_time = time.time()
                current_driver.get(target_url)
                # It's often good to wait a bit for dynamic content to load,
                # but a fixed sleep might not be optimal. Consider explicit waits if needed.
                time.sleep(3) # Allow page to render

                screenshot_file_name = generate_screenshot_filename(target_url)
                screenshot_file_path = os.path.join(SCREENSHOT_DIR, screenshot_file_name)
                
                current_driver.save_screenshot(screenshot_file_path)
                elapsed_time = round(time.time() - start_time, 2)
                print(f"✅ Screenshot saved: {screenshot_file_name} ({elapsed_time}s)")
                
                # Find the original row index this URL corresponds to
                # This uses the url_to_row_index map created earlier
                original_row_idx = url_to_row_index.get(target_url)

                if original_row_idx is not None:
                    # Store the filename and the URL for this original row index
                    # If multiple URLs from urls_to_screenshot map to the same original_row_idx
                    # (e.g., http://domain.com and http://www.domain.com were both in urls_to_screenshot
                    # but map to the same row), this will store the one processed last.
                    screenshot_filename_records[original_row_idx] = screenshot_file_name
                    successful_url_records[original_row_idx] = target_url # <<< ADDED: Store the successful URL
                
                screenshot_taken_for_url = True
                break  # Success, move to next URL

            except TimeoutException:
                print(f"⚠️ Timeout on attempt {attempt + 1} for {target_url}")
                if attempt == MAX_TRIES - 1:
                    failed_screenshots.append(f"{target_url} | Timeout after {MAX_TRIES} attempts")
            except WebDriverException as e:
                print(f"⚠️ WebDriverException on attempt {attempt + 1} for {target_url}: {str(e)[:100]}...") # Print first 100 chars of error
                if attempt == MAX_TRIES - 1:
                    failed_screenshots.append(f"{target_url} | WebDriverException: {e}")
                # For some WebDriver errors, restarting the driver might help
                if "target window already closed" in str(e).lower() or "session deleted" in str(e).lower():
                    print("Attempting to restart driver due to critical error.")
                    if current_driver: current_driver.quit()
                    current_driver = initialize_driver()
                    time.sleep(2)
            except Exception as e:
                print(f"🚨 Unhandled error on attempt {attempt + 1} for {target_url}: {e}")
                traceback.print_exc() # Print full traceback for unexpected errors
                if attempt == MAX_TRIES - 1:
                    failed_screenshots.append(f"{target_url} | Unhandled Error: {e}")
                break # Break from retries for unhandled errors

finally:
    if current_driver:
        current_driver.quit()
    print("\n🎉 Finished screenshot attempts and closed browser.")

# === Save failure log ===
if failed_screenshots:
    print(f"\n⚠️ {len(failed_screenshots)} URLs failed to screenshot. See {FAILURE_LOG_PATH}")
    with open(FAILURE_LOG_PATH, "w", encoding="utf-8") as f:
        for line in failed_screenshots:
            f.write(line + "\n")
else:
    print("\n👍 All targeted URLs processed for screenshots (or skipped as per rules).")


# === Add screenshot filename and Website URL to the original DataFrame ===
# Initialize new columns with empty strings or a placeholder
original_df["SnapshotFilename"] = "" # <<< MODIFIED: Column name consistent with JSON plan
original_df["Website"] = ""         # <<< ADDED: New column for the website URL

for row_index in range(len(original_df)):
    original_df.loc[row_index, "SnapshotFilename"] = screenshot_filename_records.get(row_index, "placeholder.png") # Use placeholder if no screenshot
    original_df.loc[row_index, "Website"] = successful_url_records.get(row_index, "") # Empty if no URL was successfully screenshotted for this row

# Save the modified DataFrame to a new Excel file
original_df.to_excel(EXCEL_OUTPUT, index=False)
print(f"\n📄 Saved Excel with screenshot filenames and URLs → {EXCEL_OUTPUT}")


# === Write out to JSON for frontend search ===
# Define the columns from the original DataFrame that you want in your JSON
# Ensure these column names exist in your original_df (check your input Excel for "Tribe", "City", etc.)
# If your Excel has different names, adjust them here or map them.
# For example, if Excel has "BIA Region", and you want "Region" in JSON, you'll rename later.
columns_for_json_extraction = [
    "Tribe", "City", "State", "Zipcode", # Assuming "Zipcode" is in original_df
    "Phone", "BIA Region",               # Assuming "BIA Region" is in original_df
    "SnapshotFilename", "Website"        # These are the columns we just added/populated
]

# Check if all desired columns exist in original_df
missing_cols = [col for col in columns_for_json_extraction if col not in original_df.columns]
if missing_cols:
    print(f"⚠️ Warning: The following columns are expected for JSON but not found in the Excel data: {', '.join(missing_cols)}")
    print(f"Available columns are: {', '.join(original_df.columns)}")
    # Filter to only existing columns to prevent error
    columns_for_json_extraction = [col for col in columns_for_json_extraction if col in original_df.columns]
    if "SnapshotFilename" not in columns_for_json_extraction: # Ensure these crucial ones are handled
        original_df["SnapshotFilename"] = "placeholder.png" # Add if missing
        columns_for_json_extraction.append("SnapshotFilename")
    if "Website" not in columns_for_json_extraction:
        original_df["Website"] = "" # Add if missing
        columns_for_json_extraction.append("Website")


print(f"\nExtracting columns for JSON: {columns_for_json_extraction}")
json_intermediate_df = original_df[columns_for_json_extraction].copy()

# Rename columns for the final JSON output as desired
rename_map = {
    "Zipcode": "Zip",             # Excel "Zipcode" becomes "Zip" in JSON
    "BIA Region": "Region",       # Excel "BIA Region" becomes "Region" in JSON
    # "SnapshotFilename" and "Website" are already named as desired for JSON
    # "Tribe", "City", "State", "Phone" are assumed to be named as desired
}
# Only rename columns that actually exist in json_intermediate_df
existing_rename_map = {k: v for k, v in rename_map.items() if k in json_intermediate_df.columns}
json_intermediate_df.rename(columns=existing_rename_map, inplace=True)

# Fill any NaN values with empty strings for cleaner JSON
json_intermediate_df = json_intermediate_df.fillna("")

# Convert the DataFrame to a list of dictionaries
tribal_data_list = json_intermediate_df.to_dict(orient="records")

# Write to JSON file
with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(tribal_data_list, f, indent=2)

print(f"\n💾 JSON data successfully saved to → {JSON_OUTPUT}")
print("✅ Script execution complete.")
