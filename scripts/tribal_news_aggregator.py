import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
import json
import os
from datetime import datetime
import re

# --- File Paths ---
INPUT_TRIBAL_DIRECTORY_EXCEL = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\TribalLeadership_Directory_-2947355220576375878.xlsx"
OUTPUT_ARTICLES_FILE = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\nativekin_aggregated_articles_with_tribe_region.json"
PROCESSING_REPORT_FILE = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\nativekin_processing_report.txt"

# --- Region Mapping (Example - can be expanded/refined) ---
STATE_TO_REGION_MAP = {
    'AL': 'Southeast', 'AK': 'Alaska', 'AZ': 'Southwest', 'AR': 'Southeast', 'CA': 'Pacific Southwest',
    'CO': 'Mountain Plains', 'CT': 'Northeast', 'DE': 'Northeast', 'FL': 'Southeast', 'GA': 'Southeast',
    'HI': 'Pacific', 'ID': 'Pacific Northwest', 'IL': 'Midwest', 'IN': 'Midwest', 'IA': 'Midwest',
    'KS': 'Midwest', 'KY': 'Southeast', 'LA': 'Southeast', 'ME': 'Northeast', 'MD': 'Northeast',
    'MA': 'Northeast', 'MI': 'Great Lakes', 'MN': 'Midwest', 'MS': 'Southeast', 'MO': 'Midwest',
    'MT': 'Mountain Plains', 'NE': 'Midwest', 'NV': 'Pacific Southwest', 'NH': 'Northeast', 'NJ': 'Northeast',
    'NM': 'Southwest', 'NY': 'Northeast', 'NC': 'Southeast', 'ND': 'Midwest', 'OH': 'Midwest',
    'OK': 'Oklahoma/Southern Plains', 'OR': 'Pacific Northwest', 'PA': 'Northeast', 'RI': 'Northeast', 'SC': 'Southeast',
    'SD': 'Midwest', 'TN': 'Southeast', 'TX': 'Southwest', 'UT': 'Mountain Plains', 'VT': 'Northeast',
    'VA': 'Southeast', 'WA': 'Pacific Northwest', 'WV': 'Southeast', 'WI': 'Great Lakes', 'WY': 'Mountain Plains',
    'DC': 'Mid-Atlantic', # For BIA/Federal
    'US': 'National' # For national organizations
}

# --- Helper Functions (Defined at the top for scope) ---

def get_region_from_state(state_abbr):
    """Maps a state abbreviation to a predefined region."""
    return STATE_TO_REGION_MAP.get(state_abbr.upper(), 'Unknown Region')

def find_news_section_url(base_url):
    """
    Attempts to find a prominent news/media section URL on a given website.
    This is heuristic and looks for common patterns.
    """
    common_news_paths = [
        "news", "press-releases", "media", "announcements", "updates", "blog",
        "newsroom", "currents", "publications", "news-media"
    ]
    headers = {'User-Agent': 'Mozilla/50 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    # Prioritize exact matches in the path or as subdomains
    for path in common_news_paths:
        test_url = urljoin(base_url.rstrip('/') + '/', path + '/') # Ensure trailing slash for join
        try:
            response = requests.head(test_url, headers=headers, timeout=5)
            if response.status_code == 200:
                return test_url
        except requests.exceptions.RequestException:
            pass
    
    # Try appending common paths to the main URL if direct subdirectories failed
    for path in common_news_paths:
        test_url = urljoin(base_url, path) # Without ensuring trailing slash
        try:
            response = requests.head(test_url, headers=headers, timeout=5)
            if response.status_code == 200:
                return test_url
        except requests.exceptions.RequestException:
            pass

    # If no specific news path is found, try the base URL itself as a last resort
    # if it looks like a news site (e.g., has 'news' in domain).
    if 'news' in urlparse(base_url).netloc.lower():
         return base_url # Main domain is news-focused
    
    return base_url # Default to the base URL if no specific news section found

def find_rss_feed(url):
    """
    Attempts to find the RSS feed URL for a given website URL or news section.
    Returns the RSS URL if found and appears valid, None otherwise.
    """
    common_rss_paths = [
        "/feed/", "/rss/", "/rss.xml", "/blog/feed/", "/blog/rss/",
        "/news/feed/", "/atom.xml", "/wp-json/wp/v2/posts?_embed&feed=rss2",
        "/feed/rss/", "/feed/atom/", "/category/news/feed/"
    ]
    headers = {'User-Agent': 'Mozilla/50 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    for path in common_rss_paths:
        test_url = urljoin(url, path)
        try:
            # Use HEAD request for efficiency first
            response = requests.head(test_url, headers=headers, timeout=3)
            if response.status_code == 200 and ('xml' in response.headers.get('Content-Type', '')):
                return test_url
        except requests.exceptions.RequestException:
            pass
    
    # Fallback to GET and check content if HEAD didn't work for common paths or HTML
    try:
        response = requests.get(url, headers=headers, timeout=7)
        response.raise_for_status()
        
        # Check for HTML link tags
        soup = BeautifulSoup(response.text, 'html.parser')
        feed_link = soup.find('link', rel='alternate', type=['application/rss+xml', 'application/atom+xml'])
        if feed_link and 'href' in feed_link.attrs:
            rss_url = feed_link['href']
            if not rss_url.startswith(('http://', 'https://')):
                rss_url = urljoin(url, rss_url)
            # Make a quick GET request to confirm the content is actually XML
            try:
                rss_content_check = requests.get(rss_url, headers=headers, timeout=5)
                if rss_content_check.status_code == 200 and ('xml' in rss_content_check.headers.get('Content-Type', '') or '<rss' in rss_content_check.text.lower() or '<feed' in rss_content_check.text.lower()):
                    return rss_url
            except requests.exceptions.RequestException:
                pass

        # If no explicit link, try looking for XML content type in the main page response itself
        if 'xml' in response.headers.get('Content-Type', '') and ('<rss' in response.text.lower() or '<feed' in response.text.lower()):
            return url # The main URL itself might be the feed

    except requests.exceptions.RequestException:
        pass
    return None

def check_feed_has_entries(feed_url):
    """Parses an RSS feed and returns True if it contains entries, False otherwise."""
    try:
        feed = feedparser.parse(feed_url)
        # Check for bozo (parse errors) AND if there are any entries
        return bool(feed.entries) and not feed.bozo
    except Exception:
        return False

def get_articles_from_rss(rss_url, max_entries=10):
    """
    Parses an RSS feed and extracts information from its entries.
    Returns a list of dictionaries, each representing an article.
    """
    articles = []
    try:
        feed = feedparser.parse(rss_url)
        if feed.bozo: return []

        for i, entry in enumerate(feed.entries):
            if i >= max_entries: break

            title = entry.get('title', 'No Title')
            link = entry.get('link', 'No Link')
            published_parsed = entry.get('published_parsed')
            published = datetime(*published_parsed[:6]).strftime('%Y-%m-%d %H:%M:%S') if published_parsed else entry.get('published', 'No Date')
            
            summary = entry.get('summary') or entry.get('description')
            if not summary and 'content' in entry and entry['content']:
                if isinstance(entry['content'], list) and len(entry['content']) > 0:
                    summary = entry['content'][0].get('value', '')
            summary = BeautifulSoup(summary or '', 'html.parser').get_text()
            summary = (summary[:500] + '...') if len(summary) > 500 else summary

            articles.append({
                'source_url': rss_url, # This will be the RSS feed URL
                'title': title,
                'link': link,
                'published': published,
                'summary': summary.strip()
            })
    except Exception as e:
        pass
    return articles

def scrape_news_articles(news_url, max_articles=5):
    """
    Attempts to scrape recent news articles from a general news page.
    This is a heuristic scraper and might need customization per site based on its HTML structure.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    articles = []
    try:
        response = requests.get(news_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Priority 1: Look for common containers of articles
        containers = soup.find_all(['article', 'div', 'section'], class_=re.compile(r'news-item|post|article|story|entry|hentry|listing-item|card|blog-post|news-listing|story-listing', re.I))

        # Priority 2: Fallback to broader search within main content areas
        if not containers:
            main_content_areas = soup.find_all(['main', 'div', 'section'], id=re.compile(r'main-content|content|body|primary|page-content', re.I))
            temp_links_from_broad_scrape = []
            for area in main_content_areas:
                links = area.find_all('a', href=True, text=True) # Find all links with text
                for link_tag in links:
                    if len(temp_links_from_broad_scrape) >= max_articles: break # Limit early
                    link_text = link_tag.get_text(strip=True)
                    link_url = urljoin(news_url, link_tag['href'])

                    # Filter out non-article links based on common patterns and link text length
                    if (len(link_text) > 20 and # Title should be reasonably long
                        re.search(r'news|article|story|post|press|media|release', link_url, re.I) and # URL hints
                        not re.search(r'category|tag|archive|page|contact|about|login|subscribe|#', link_url, re.I) and # Exclude common non-article links
                        not link_url.endswith(('.pdf', '.doc', '.docx', '.jpg', '.png'))): # Exclude documents/images
                        
                        temp_links_from_broad_scrape.append({'title': link_text, 'link': link_url})
            # If broad scrape finds some, use them
            if temp_links_from_broad_scrape:
                articles.extend([{'source_url': news_url, 'title': item['title'], 'link': item['link'], 'published': "Date N/A (Scraped)", 'summary': ""} for item in temp_links_from_broad_scrape])


        # Refine articles from identified containers (if any found and no broad scrape articles yet)
        if containers and not articles: # Only process containers if broad scrape didn't already find enough
            for container in containers:
                if len(articles) >= max_articles: break
                
                link_tag = container.find('a', href=True)
                title_tag = container.find(['h1', 'h2', 'h3', 'h4', 'h5'], class_=re.compile(r'title|heading|post-title|entry-title', re.I))
                summary_tag = container.find(['p', 'div'], class_=re.compile(r'summary|description|excerpt|entry-content', re.I))
                
                title = title_tag.get_text(strip=True) if title_tag else (link_tag.get_text(strip=True) if link_tag else None)
                link = urljoin(news_url, link_tag['href']) if link_tag else None
                
                summary = summary_tag.get_text(strip=True) if summary_tag else ""
                summary = BeautifulSoup(summary, 'html.parser').get_text() # Clean HTML tags from summary
                summary = (summary[:500] + '...') if len(summary) > 500 else summary
                
                if title and link and len(title) > 15 and re.search(r'news|article|story|post|press|media', link.lower()):
                    if not any(a.get('link') == link for a in articles): # Avoid duplicates
                        articles.append({
                            'source_url': news_url, # Original base URL as the source
                            'title': title,
                            'link': link,
                            'published': "Date N/A (Scraped)",
                            'summary': summary.strip()
                        })
        
    except requests.exceptions.RequestException as e:
        pass
    except Exception as e:
        pass

    return articles

# --- Main Aggregation Logic ---
def main():
    print("--- Starting Fully Automated Tribal News Aggregation ---")

    # --- Step 1: Load Tribal Directory Data ---
    tribes_data = []
    try:
        # Read the Excel file. Assuming the first sheet and relevant columns.
        df_tribes = pd.read_excel(INPUT_TRIBAL_DIRECTORY_EXCEL, engine='openpyxl')
        
        # CORRECTED COLUMN NAMES based on your traceback
        tribe_name_col = 'Tribe Full Name' # Confirmed from your output
        state_col = 'State'               # Confirmed from your output
        website_col = 'Website'           # Confirmed from your output

        # Basic validation for column existence
        if not all(col in df_tribes.columns for col in [tribe_name_col, state_col, website_col]):
            print(f"Error: Missing expected columns in Excel. Found: {df_tribes.columns.tolist()}")
            print(f"Expected: '{tribe_name_col}', '{state_col}', '{website_col}'")
            return
        
        for index, row in df_tribes.iterrows():
            tribe_name = str(row[tribe_name_col]).strip()
            state_abbr = str(row[state_col]).strip()
            website_url = str(row[website_col]).strip()

            # Filter out entries with no valid tribe name or website URL
            if tribe_name and website_url and website_url.startswith('http'):
                tribes_data.append({
                    'TribeName': tribe_name,
                    'StateAbbr': state_abbr,
                    'WebsiteURL': website_url,
                    'Region': get_region_from_state(state_abbr) # Assign region based on state
                })
        print(f"Loaded {len(tribes_data)} tribes from the directory.")

    except FileNotFoundError:
        print(f"Error: Tribal directory Excel file not found at {INPUT_TRIBAL_DIRECTORY_EXCEL}.")
        print("Please ensure the path is correct and the file exists.")
        return
    except Exception as e:
        print(f"Error reading tribal directory Excel file: {e}")
        return

    # --- Step 2: Iterate through Tribes, Find News, Pull Articles, and Enrich ---
    all_aggregated_articles = []
    processing_report_lines = []

    processing_report_lines.append(f"--- Tribal News Aggregation Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    processing_report_lines.append(f"Total tribes in directory: {len(tribes_data)}\n")
    
    # Store unique sources that yielded articles, along with how they were pulled, for the report
    successful_sources_for_report = {}

    for i, tribe_info in enumerate(tribes_data):
        tribe_name = tribe_info['TribeName']
        base_url = tribe_info['WebsiteURL']
        region = tribe_info['Region']
        
        print(f"\n[{i+1}/{len(tribes_data)}] Processing Tribe: {tribe_name} (URL: {base_url})")
        processing_report_lines.append(f"\nProcessing Tribe: {tribe_name} (URL: {base_url})")

        # Step 2.1: Find the most promising news section URL
        news_url_to_pull = find_news_section_url(base_url)
        if news_url_to_pull != base_url: # Only if a specific news section was found
            print(f"  Identified news section: {news_url_to_pull}")
            processing_report_lines.append(f"  News Section Identified: {news_url_to_pull}")
        else:
            print(f"  No specific news section found. Will try base URL: {base_url}")
            processing_report_lines.append(f"  No specific news section found. Will try Base URL: {base_url}")

        articles_from_current_tribe = []
        pull_method = "None"
        source_identifier_for_report = news_url_to_pull # Default to the identified news_url

        # Step 2.2: Attempt RSS Pull
        rss_feed_url = find_rss_feed(news_url_to_pull)
        if rss_feed_url and check_feed_has_entries(rss_feed_url):
            articles_from_current_tribe = get_articles_from_rss(rss_feed_url, max_entries=10)
            pull_method = "RSS"
            source_identifier_for_report = rss_feed_url # Use RSS URL as primary identifier if successful
            print(f"  Pulled {len(articles_from_current_tribe)} articles via RSS from {rss_feed_url}")
            processing_report_lines.append(f"  Pulled {len(articles_from_current_tribe)} articles via RSS from {rss_feed_url}")
        else:
            # Step 2.3: Fallback to Direct Web Scraping if RSS fails/is empty
            print(f"  No valid RSS feed found for {news_url_to_pull} (or empty). Attempting direct scrape...")
            articles_from_current_tribe = scrape_news_articles(news_url_to_pull, max_articles=5) # Try scraping the identified news_url
            if articles_from_current_tribe:
                pull_method = "Scrape"
                print(f"  Pulled {len(articles_from_current_tribe)} articles via Scrape from {news_url_to_pull}")
                processing_report_lines.append(f"  Pulled {len(articles_from_current_tribe)} articles via Scrape from {news_url_to_pull}")
            else:
                # Final Fallback: If scraping the news_url failed, try scraping the original base_url
                if news_url_to_pull != base_url: # Only if we tried a different news_url first
                    articles_from_current_tribe = scrape_news_articles(base_url, max_articles=5)
                    if articles_from_current_tribe:
                        pull_method = "Scrape (Base URL Fallback)"
                        print(f"  Pulled {len(articles_from_current_tribe)} articles via Scrape from Base URL: {base_url}")
                        processing_report_lines.append(f"  Pulled {len(articles_from_current_tribe)} articles via Scrape from Base URL: {base_url}")
                    else:
                        print(f"  No articles pulled from RSS or Scrape for {tribe_name}.")
                        processing_report_lines.append(f"  No articles pulled from RSS or Scrape.")
                else:
                    print(f"  No articles pulled from RSS or Scrape for {tribe_name}.")
                    processing_report_lines.append(f"  No articles pulled from RSS or Scrape.")

        # Enrich articles with Tribe and Region and add to master list
        if articles_from_current_tribe:
            successful_sources_for_report[tribe_name] = {'url': base_url, 'pull_method': pull_method, 'articles_count': len(articles_from_current_tribe)}
            for article in articles_from_current_tribe:
                article['tribe'] = tribe_name
                article['region'] = region
                article['source_original_directory_url'] = base_url # URL from the directory
                article['source_pull_url'] = source_identifier_for_report # Actual URL used for pull (RSS or scrape)
                article['pull_method'] = pull_method # Track how it was pulled
                all_aggregated_articles.append(article)
        
        time.sleep(1.5) # Be polite to websites


    print(f"\n--- Aggregation Complete ---")
    print(f"Total articles collected: {len(all_aggregated_articles)}")
    print(f"Successfully pulled articles from {len(successful_sources_for_report)} unique tribal sources.")

    processing_report_lines.append(f"\n--- Aggregation Summary ---")
    processing_report_lines.append(f"Total articles collected: {len(all_aggregated_articles)}")
    processing_report_lines.append(f"Unique sources yielding articles: {len(successful_sources_for_report)}")
    for tribe, info in successful_sources_for_report.items():
        processing_report_lines.append(f"  - {tribe}: {info['articles_count']} articles via {info['pull_method']} from {info['url']}")


    # Sort articles (Tribe -> Region -> Date)
    def sort_key(article):
        tribe_key = article.get('tribe', 'Unknown Tribe').lower()
        region_key = article.get('region', 'Unknown Region').lower()
        published_date_str = article.get('published')

        try:
            date_key = datetime.strptime(published_date_str, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            date_key = datetime.min # Place articles with unparseable dates at the very beginning of their group for consistency

        return (tribe_key, region_key, date_key)

    all_aggregated_articles.sort(key=sort_key, reverse=True) # Most recent articles first within each group

    # --- Step 3: Save Aggregated Articles to JSON ---
    output_dir = os.path.dirname(OUTPUT_ARTICLES_FILE)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        with open(OUTPUT_ARTICLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_aggregated_articles, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved {len(all_aggregated_articles)} articles to {OUTPUT_ARTICLES_FILE}")
        processing_report_lines.append(f"Successfully saved aggregated articles to: {OUTPUT_ARTICLES_FILE}")
    except Exception as e:
        print(f"Error saving aggregated articles to JSON file: {e}")
        processing_report_lines.append(f"Error saving aggregated articles: {e}")

    # --- Step 4: Save Processing Report ---
    try:
        with open(PROCESSING_REPORT_FILE, 'w', encoding='utf-8') as f:
            for line in processing_report_lines:
                f.write(line + '\n')
        print(f"Processing report saved to: {PROCESSING_REPORT_FILE}")
    except Exception as e:
        print(f"Error saving processing report: {e}")

    print("\n--- All Processes Complete ---")

if __name__ == "__main__":
    main()