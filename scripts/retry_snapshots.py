import os
import time
import tldextract
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# CONFIG
FAILURE_LOG = "failures.log"
SCREENSHOT_DIR = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\hpsnaps"
RETRY_LOG = "failures_retry.log"
TIMEOUT_SECONDS = 30

# Filter failure types you care about
RETRY_KEYWORDS = ["timeout", "net::ERR_NAME_NOT_RESOLVED"]

# Parse failure log
def extract_failed_urls():
    urls = []
    with open(FAILURE_LOG, 'r') as f:
        for line in f:
            for keyword in RETRY_KEYWORDS:
                if keyword in line:
                    parts = line.strip().split('|')
                    if len(parts) >= 1:
                        url = parts[0].strip()
                        if url.startswith("http"):
                            urls.append(url)
    return list(set(urls))  # dedupe

# Clean domain name for saving
def get_domain_name(url):
    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}".replace(".", "")  # get rid of dots

# Take snapshot
def snapshot_url(driver, url, save_path):
    try:
        driver.set_page_load_timeout(TIMEOUT_SECONDS)
        driver.get(url)
        time.sleep(5)
        driver.save_screenshot(save_path)
        return True
    except Exception as e:
        with open(RETRY_LOG, "a") as log:
            log.write(f"{url} | Message: {str(e)}\n")
        return False

# Chrome headless setup
def setup_browser():
    options = Options()
    options.headless = True
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    return webdriver.Chrome(options=options)

# MAIN
if __name__ == "__main__":
    failed_urls = extract_failed_urls()
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)

    driver = setup_browser()

    for url in failed_urls:
        domain = get_domain_name(url)
        save_path = os.path.join(SCREENSHOT_DIR, f"{domain}.png")
        if os.path.exists(save_path):
            continue  # Already succeeded
        print(f"🔁 Retrying {url}")
        snapshot_url(driver, url, save_path)

    driver.quit()
    print("✅ Retry pass completed.")
