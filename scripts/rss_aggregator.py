import os
import json
import feedparser # pip install feedparser
from datetime import datetime
import time # For formatting dates
from bs4 import BeautifulSoup # pip install beautifulsoup4
import logging # For improved logging
import socket # For global timeout

# --- Configuration ---
# Assuming the script is in a 'scripts' directory, and 'media' and 'logs' are siblings to 'scripts'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, '..') 

MEDIA_DIR = os.path.join(PROJECT_ROOT, 'media')
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')

FEED_DEFINITIONS_FILE = os.path.join(MEDIA_DIR, 'nativekin_feeds.json') 
AGGREGATED_ARTICLES_FILE = os.path.join(MEDIA_DIR, 'nativekin_aggregated_articles.json') 
LOG_FILE = os.path.join(LOG_DIR, 'rss_aggregator.log') 

# Define network timeouts (in seconds)
# FEEDPARSER_TIMEOUT = 15 # Timeout for individual feed parsing -- REMOVED as it's not a direct arg
SOCKET_DEFAULT_TIMEOUT = 20 # Global timeout for all socket operations

# --- Setup Logging ---
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filemode='a' # Append to log file
)
# Also print logs to console for immediate feedback
# Remove existing handlers before adding new ones to avoid duplicate logs if script is re-run in same session
for handler in logging.getLogger().handlers[:]:
    logging.getLogger().removeHandler(handler)

# Re-add file handler (basicConfig does this, but let's be explicit if we clear)
file_handler = logging.FileHandler(LOG_FILE, mode='a') # Ensure append mode
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logging.getLogger().addHandler(file_handler)


console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO) # You might want logging.DEBUG for more verbose console output
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)
logging.getLogger().setLevel(logging.INFO) # Ensure root logger level is set


# --- Helper function to strip HTML ---
def strip_html(html_content):
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        logging.warning(f"BeautifulSoup parsing error: {e}. Returning raw content.")
        return str(html_content) # Fallback to string representation

# --- Main Script ---
def main():
    # Set a global timeout for all socket operations to prevent indefinite hangs
    try:
        socket.setdefaulttimeout(SOCKET_DEFAULT_TIMEOUT)
        logging.info(f"Global socket timeout set to {SOCKET_DEFAULT_TIMEOUT} seconds.")
    except Exception as e:
        logging.warning(f"Could not set global socket timeout: {e}")


    logging.info("Starting RSS feed aggregation script.")

    try:
        with open(FEED_DEFINITIONS_FILE, 'r', encoding='utf-8') as f:
            tribal_news_sources = json.load(f)
        logging.info(f"Successfully loaded {len(tribal_news_sources)} feed definitions from {FEED_DEFINITIONS_FILE}")
    except FileNotFoundError:
        logging.error(f"CRITICAL: Feed definitions file not found at {FEED_DEFINITIONS_FILE}")
        raise SystemExit(f"Error: Feed definitions file not found at {FEED_DEFINITIONS_FILE}")
    except json.JSONDecodeError as e:
        logging.error(f"CRITICAL: Error decoding JSON from {FEED_DEFINITIONS_FILE}: {e}")
        raise SystemExit(f"Error: Malformed JSON in {FEED_DEFINITIONS_FILE}")
    except Exception as e:
        logging.error(f"CRITICAL: Error reading feed definitions file {FEED_DEFINITIONS_FILE}: {e}")
        raise SystemExit(f"Error loading feed list: {e}")

    aggregated_articles = []
    processed_feed_count = 0
    failed_feed_count = 0
    total_feeds_to_process = len(tribal_news_sources)

    for index, source_info in enumerate(tribal_news_sources):
        source_name = source_info.get('name', 'Unknown Source')
        feed_url = source_info.get('url')
        tribe_name = source_info.get('tribe', 'N/A')
        is_national = source_info.get('national', False)

        logging.info(f"Processing feed {index + 1}/{total_feeds_to_process}: '{source_name}' from {feed_url}")

        if not feed_url:
            logging.warning(f"Skipping source '{source_name}' due to missing URL.")
            failed_feed_count += 1
            continue
        
        feed_data = None 
        try:
            print(f"  Attempting to parse: {feed_url} ...") 
            # REMOVED: timeout=FEEDPARSER_TIMEOUT from this call
            feed_data = feedparser.parse(feed_url) 
            print(f"  Finished parsing attempt for: {feed_url}")

            if feed_data.bozo:
                bozo_message = repr(feed_data.bozo_exception)
                logging.warning(f"Feed '{source_name}' may be ill-formed. Error: {bozo_message}")
            
            entries_processed_count = 0
            if feed_data and feed_data.entries: 
                for entry in feed_data.entries[:5]: # Process top 5 entries
                    title = entry.get('title', 'No Title Provided')
                    link = entry.get('link', '')

                    published_date_str = ""
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            published_date_str = time.strftime('%Y-%m-%d %H:%M:%S', entry.published_parsed)
                        except TypeError: # Handle cases where published_parsed might be None despite hasattr
                             logging.warning(f"Could not format 'published_parsed' for an entry in '{source_name}'. It might be None. Falling back.")
                             published_date_str = entry.get('published', '')
                        except Exception as ex_date:
                            logging.warning(f"Error formatting 'published_parsed' for an entry in '{source_name}': {ex_date}. Falling back.")
                            published_date_str = entry.get('published', '') 
                    else:
                        published_date_str = entry.get('published', '') 

                    summary_html = entry.get('summary', entry.get('description', '')) 
                    summary_text = strip_html(summary_html)
                    summary_truncated = (summary_text[:297] + '...') if len(summary_text) > 300 else summary_text

                    aggregated_articles.append({
                        'title': title,
                        'link': link,
                        'published': published_date_str,
                        'summary': summary_truncated,
                        'source_name': source_name,
                        'tribe': tribe_name,
                        'national': is_national
                    })
                    entries_processed_count += 1
            
                if entries_processed_count > 0:
                    logging.info(f"Successfully parsed {entries_processed_count} entries from '{source_name}'.")
                elif not (feed_data and feed_data.entries): 
                    logging.info(f"No entries found in feed '{source_name}' (feed_data.entries was empty or feed_data itself was problematic).")
                else:
                    logging.info(f"Processed 0 entries (from top 5 attempted) from '{source_name}'.")
            else: 
                logging.warning(f"No entries could be processed for '{source_name}'. Feed data might be empty or errored before entry processing (feed_data: {feed_data is not None}, feed_data.entries: {hasattr(feed_data, 'entries') and feed_data.entries is not None}).")


            processed_feed_count +=1

        except socket.timeout:
            logging.error(f"SOCKET TIMEOUT processing feed '{source_name}' ({feed_url}) after {SOCKET_DEFAULT_TIMEOUT}s (global timeout). This feed is unresponsive or very slow.")
            print(f"  TIMEOUT for: {feed_url}")
            failed_feed_count += 1
        except Exception as e: 
            logging.error(f"GENERAL EXCEPTION processing feed '{source_name}' ({feed_url}): {e}", exc_info=True) # Log full traceback for general exceptions
            print(f"  ERROR processing: {feed_url} - {e}")
            failed_feed_count += 1

    logging.info(f"Feed processing complete. Successfully attempted to process: {processed_feed_count}, Failed/Skipped: {failed_feed_count}")

    try:
        os.makedirs(MEDIA_DIR, exist_ok=True)
        with open(AGGREGATED_ARTICLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(aggregated_articles, f, indent=2, ensure_ascii=False)
        logging.info(f"Successfully saved {len(aggregated_articles)} aggregated articles to {AGGREGATED_ARTICLES_FILE}")
    except Exception as e:
        logging.error(f"CRITICAL: Error writing output JSON to {AGGREGATED_ARTICLES_FILE}: {e}")
        raise SystemExit(f"Error saving aggregated articles: {e}")

    logging.info("RSS feed aggregation script finished successfully.")
    print(f"\n✅ Aggregated {len(aggregated_articles)} articles from {total_feeds_to_process} feed sources defined.")
    print(f"   Successfully processed content from {processed_feed_count - failed_feed_count} feeds.") # More accurate count
    print(f"   Feeds that failed or were skipped: {failed_feed_count}.")
    print(f"   Check '{LOG_FILE}' for detailed logs.")

if __name__ == '__main__':
    main()
