import os
import time
import re
import json
import traceback
import pandas as pd
import tldextract
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException

# === CONFIGURATION ===
EXCEL_INPUT = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\data\TribalLeadership_Sample_WithScreenshots.xlsx"
EXCEL_OUTPUT = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\scripts\TribalLeadership_WithScreenshots.xlsx"
FAILURE_LOG_PATH = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\scripts\failures.log"
SCREENSHOT_DIR = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\hpsnaps"
JSON_OUTPUT = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\data\tribalDirectory.json"
TIMEOUT = 15
MAX_TRIES = 3
RESTART_INTERVAL = 25

SKIP_DOMAINS = {
    "google.com", "bing.com", "yahoo.com", "aol.com", "msn.com", "ask.com",
    "icloud.com", "outlook.com", "facebook.com", "instagram.com", "twitter.com"
}

os.makedirs(os.path.dirname(EXCEL_OUTPUT), exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(JSON_OUTPUT), exist_ok=True)

# === EXTRACT URLs FROM EXCEL ===
excel_data = pd.read_excel(EXCEL_INPUT, sheet_name=None)
df_combined = pd.concat(excel_data.values(), ignore_index=True)
original_df = df_combined.copy()

def extract_urls(text):
    pattern = r'\b(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?'
    return re.findall(pattern, str(text))

all_urls = []
url_to_row = {}

for idx, row in original_df.iterrows():
    for cell in row.values:
        for url in extract_urls(cell):
            norm_url = 'http://' + url if not url.startswith('http') else url
            if norm_url not in url_to_row:
                url_to_row[norm_url] = idx
            all_urls.append(norm_url)

# Deduplicate by root domain (no scheme or subdomain)
def strip_to_domain(url):
    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}"

domain_seen = set()
unique_urls = []
for u in all_urls:
    domain = strip_to_domain(u)
    if domain in SKIP_DOMAINS:
        print(f"⛔ Skipping known bad domain: {domain}")
        continue
    if domain not in domain_seen:
        domain_seen.add(domain)
        unique_urls.append(u)

# === Setup browser ===
def get_driver():
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1600,1200")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(TIMEOUT)
    return driver

screenshot_records = {}
failures = []

def domain_filename(url):
    ext = tldextract.extract(url)
    return f"{ext.domain}.png"

driver = get_driver()

try:
    for idx, url in enumerate(unique_urls):
        if idx > 0 and idx % RESTART_INTERVAL == 0:
            driver.quit()
            driver = get_driver()

        start = time.time()
        for attempt in range(MAX_TRIES):
            try:
                print(f"\n🧭 Trying {url} (attempt {attempt + 1})...")
                driver.get(url)
                time.sleep(3)
                filename = domain_filename(url)
                filepath = os.path.join(SCREENSHOT_DIR, filename)
                driver.save_screenshot(filepath)
                elapsed = round(time.time() - start, 2)
                print(f"✅ {filename} ({elapsed}s)")
                row_idx = url_to_row.get(url)
                if row_idx is not None and row_idx not in screenshot_records:
                    screenshot_records[row_idx] = filename
                break  # success, exit retry loop
            except (TimeoutException, WebDriverException) as e:
                print(f"⚠️ Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == MAX_TRIES - 1:
                    failures.append(f"{url} | {e} | {round(time.time() - start, 2)}s")
            except Exception as e:
                print(f"🚨 Unhandled error on {url}: {e}")
                traceback.print_exc()
                failures.append(f"{url} | {e} | {round(time.time() - start, 2)}s")
                break
finally:
    driver.quit()
    print("🎉 Finished all URLs and closed browser.")

# === Save failure log ===
with open(FAILURE_LOG_PATH, "w", encoding="utf-8") as f:
    for line in failures:
        f.write(line + "\n")

# === Add screenshot filename to Excel ===
original_df["Screenshot Filename"] = [
    screenshot_records.get(i, "") for i in range(len(original_df))
]
original_df.to_excel(EXCEL_OUTPUT, index=False)
print(f"\n📄 Saved Excel with filenames → {EXCEL_OUTPUT}")
print(f"🪵 Logged failures → {FAILURE_LOG_PATH}")

# === Write out to JSON for frontend search ===
json_df = original_df[["Tribe", "City", "State", "Zipcode", "Phone", "Screenshot Filename", "BIA Region"]].copy()
json_df.columns = ["Tribe", "City", "State", "Zip", "Phone", "SnapshotFilename", "Region"]
json_df = json_df.fillna("")
tribal_data = json_df.to_dict(orient="records")

with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(tribal_data, f, indent=2)

print(f"🧭 JSON data saved to → {JSON_OUTPUT}")
print("✅ Script execution complete.")
