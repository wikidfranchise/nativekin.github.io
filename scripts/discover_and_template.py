import requests
import feedparser
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
import json
import pandas as pd
import os
from datetime import datetime
import re

# --- Master List of Potential News Sources ---
# This list now contains all 222 potential sources identified.
# Removed many explicit /feed/ or /rss/ suffixes for initial discovery,
# as the find_rss_feed function will try common patterns.
ALL_POTENTIAL_SOURCES = sorted(list(set([
    # Initial 21/22 feeds
    "https://ictnews.org/",
    "https://www.indianz.com/",
    "https://www.nativenewsonline.net/",
    "https://www.nativeamericacalling.com/",
    "https://www.hcn.org/",
    "https://thecirclenews.org/",
    "https://osagenews.org/",
    "https://www.mvskokemedia.com/",
    "https://www.spokanetribe.com/",
    "https://nativenewsonline.net/",
    "https://www.powwows.com/",
    "https://www.narf.org/",
    "https://www.culturalsurvival.org/",
    "https://www.meskwaki.org/",
    "https://www.cowlitz.org/",
    "https://ltbbodawa-nsn.gov/",
    "https://www.yakama.com/",
    "https://www.wbur.org/",
    "https://www.kxci.org/",
    "https://www.koahnic.org/",
    "https://www.bia.gov/",

    # New 201 URLs you provided
    "https://www.navajo-nsn.gov/News/",
    "https://cherokeenation.com/newsroom/",
    "https://www.choctawnation.com/news/",
    "https://chickasaw.net/News.aspx",
    "https://www.semtribe.com/news",
    "https://oglalasiouxtribe.net/news",
    "https://www.crowcreeksiouxtribe.com/news-updates",
    "https://www.rosebudsiouxtribe-nsn.gov/news",
    "https://sioux.org/news/",
    "https://standingrock.org/news-events/",
    "https://gricnews.org/",
    "https://www.srpmic-nsn.gov/news/",
    "https://www.tonation-nsn.gov/news-events",
    "http://sancarlosapache.com/category/news/",
    "https://www.wmat.nsn.us/news.html",
    "https://ftmcdowell.org/news-media/",
    "https://puebloofacoma.org/news/",
    "https://www.lagunapueblo-nsn.gov/news-events/",
    "https://www.ashiwi.org/news-events/",
    "https://www.isletapueblo.com/news/",
    "https://santaclarapueblo.org/news/",
    "https://taospueblo.com/news/",
    "https://ohkayowingeh-nsn.gov/news-events/",
    "https://jicarillaapache.org/news/",
    "https://mescaleroapachetribe.com/news/",
    "https://navajotimes.com/",
    "https://www.cherokeephoenix.org/",
    "https://www.mvskokemedia.com/",
    "https://osagenews.org/",
    "http://www.charkoosta.com/",
    "https://blackfeetnation.com/news-events/",
    "https://crowtribe.com/news/",
    "https://www.northerncheyennetribe.com/news",
    "https://www.utetribe.com/news/",
    "https://www.southernute.com/news/",
    "https://utemountainutetribe.com/news/",
    "https://gptca.org/news-events/",
    "https://www.oneidanation.org/news-events/kalihwisaks/",
    "https://www.ho-chunk.com/news/",
    "https://www.lacduflambeau.com/news/",
    "https://www.menominee-nsn.gov/news-media-events",
    "https://www.fcpotawatomi.com/news-media/",
    "https://saulttribe.com/news-media",
    "https://www.gtbindians.org/news-media/",
    "https://www.pokagonband-nsn.gov/newsroom",
    "https://lrboi-nsn.gov/news/",
    "https://www.sagchip.org/news/",
    "https://www.mohican.com/news/",
    "https://sni.org/news/",
    "https://www.akwesasne.ca/news/",
    "https://www.oneidaindiannation.com/news-media/",
    "https://www.mashantucket.com/news",
    "https://mohegan.org/news/",
    "https://www.narragansettri.gov/181/Tribal-News",
    "https://www.miccosukee.com/news",
    "https://www.semtribe.com/newsroom",
    "https://ebci.com/news/",
    "https://lumbeetribe.com/news/",
    "https://www.catawbaindiannation.com/news/",
    "https://pbcinsn.gov/news-media/",
    "https://www.choctaw.org/news/",
    "https://tunicabiloxi.org/news/",
    "https://alabama-coushatta.com/news/",
    "https://www.kttot.com/news/",
    "https://www.pascuayaqui-nsn.gov/news/",
    "https://www.tonation-nsn.gov/",
    "https://ak-chin.nsn.us/news-media/",
    "https://www.cochitipueblo.org/news-events/",
    "https://pojoaque.org/news-events/",
    "https://picuris.org/news-events/",
    "https://www.taospueblo.com/news",
    "https://sanfelipecdc.org/news/",
    "https://www.santaana.org/news/",
    "https://ohkayowingeh-nsn.gov/news/",
    "https://jicarillaapache.org/news/",
    "https://mescaleroapachetribe.com/news",
    "https://fortsillapache.com/news/",
    "https://astribe.com/news/",
    "https://cherokeenation.com/news/",
    "https://chickasaw.net/News.aspx",
    "https://www.choctawnation.com/news/",
    "https://delawarenation.com/news/",
    "https://estoo.net/news/",
    "https://miamitribeofoklahoma.net/news-events/",
    "https://modoctribe.net/news/",
    "https://osagenation-nsn.gov/news/",
    "https://pawneenation.org/news/",
    "https://peoriatribe.com/news-events/",
    "https://quapawnation.com/news/",
    "https://www.sacandfoxnation-nsn.gov/news/",
    "https://wyandotte-nation.org/news/",
    "https://wichitatribes.com/news/",
    "https://comanchenation.com/news/",
    "https://kiowatribe.org/news/",
    "https://cheyenneandarapaho.org/news/",
    "https://www.potawatomi.org/news/",
    "https://www.pbpindiantribe.com/news/",
    "https://omahatribe.com/news/",
    "https://www.winnebagotribe.com/news/",
    "https://fsst.org/news/",
    "https://swo-nsn.gov/news/",
    "https://www.spiritlakenation.com/news/",
    "https://tmchi.org/news/",
    "https://www.colvilletribes.com/news/",
    "https://yakama.com/news/",
    "https://nooksacktribe.org/news/",
    "https://www.muckleshoot.nsn.us/news/",
    "https://snoqualmietribe.us/news/",
    "https://www.suquamish.nsn.us/news/",
    "https://jamestowntribe.org/news-media/",
    "https://www.skokomish.org/news/",
    "https://puyalluptribe-nsn.gov/newsroom/",
    "https://www.nisqually-nsn.gov/news/",
    "https://www.grandronde.org/news/",
    "https://www.ctsi.nsn.us/news/",
    "https://www.coquilletribe.org/news/",
    "https://ctuir.org/news/",
    "https://warmsprings-nsn.gov/news/",
    "https://klamathtribes.org/news/",
    "https://www.karuk.us/index.php/news-events",
    "https://www.yuroktribe.org/news/",
    "https://www.hoopavalley.net/news",
    "https://www.rvit.org/news/",
    "https://big-valley.net/news/",
    "https://www.drycreekrancheria.com/news/",
    "https://gratonrancheria.com/news/",
    "https://middletownrancheria.com/news/",
    "https://www.colusa-nsn.gov/news/",
    "https://www.morongonation.org/news/",
    "https://www.sanmanuel-nsn.gov/news/",
    "https://www.aguacaliente.org/news/",
    "https://viejasbandofkumeyaay.org/news/",
    "https://www.barona-nsn.gov/news/",
    "https://www.sycuan.com/news/",
    "https://campo-nsn.gov/news/",
    "https://lajollaindians.com/news/",
    "https://mesagrandebandofdieguenomissionindians.org/news/",
    "https://www.paumatribe.com/news/",
    "https://www.rincon-nsn.gov/news/",
    "https://www.santaysabel.org/news/",
    "https://www.29palmstribe.org/news/",
    "https://www.cabazonindians.com/news/",
    "https://www.pechanga.com/news/",
    "https://www.aguacaliente.org/newsroom/",
    "https://soboba-nsn.gov/news/",
    "https://quechantribe.com/news/",
    "https://www.cocopah.com/news/",
    "https://fortmojave.com/news-media/",
    "https://hualapai-nsn.gov/news-events/",
    "https://yavapai-apache.org/news-events/",
    "https://tontoapache.org/news-events/",
    "https://ak-chin.nsn.us/news/",
    "https://www.pascuayaqui-nsn.gov/newsroom/",
    "https://www.navajo-nsn.gov/news-room/",
    "https://mescaleroapachetribe.com/news-events/",
    "https://jemezpueblo.org/news/",
    "https://zia.gov/news/",
    "https://santodomingopueblo.org/news-events/",
    "https://sanipueblo.org/news-events/",
    "https://nambepueblo.org/news/",
    "https://ohkayowingeh-nsn.gov/newsroom/",
    "https://picuris.org/news/",
    "https://taospueblo.com/media/",
    "https://www.rnbs.k12.nm.us/news/",
    "https://www.lagunapueblo-nsn.gov/news/",
    "https://puebloofacoma.org/news-media/",
    "https://mescaleroapachetribe.com/newsroom/",
    "https://www.navajo-nsn.gov/press-releases/",
    "https://jicarillaapache.org/news-events/",
    "https://utemountainutetribe.com/news-events/",
    "https://www.southernute.com/latest-news/",
    "https://www.utetribe.com/newsroom/",
    "https://cherokeenation.com/newsroom/press-releases/",
    "https://chickasaw.net/News/All-News.aspx",
    "https://www.choctawnation.com/news/all-news/",
    "https://www.mvskokemedia.com/news-releases/",
    "https://osagenation-nsn.gov/news-room/",
    "https://quapawnation.com/press-releases/",
    "https://www.sacandfoxnation-nsn.gov/press-releases/",
    "https://wyandotte-nation.org/press-releases/",
    "https://www.potawatomi.org/press-releases/",
    "https://www.pbpindiantribe.com/press-releases/",
    "https://omahatribe.com/press-releases/",
    "https://www.winnebagotribe.com/press-releases/",
    "https://fsst.org/press-releases/",
    "https://swo-nsn.gov/press-releases/",
    "https://www.spiritlakenation.com/press-releases/",
    "https://tmchi.org/press-releases/",
    "https://www.colvilletribes.com/press-releases/",
    "https://nooksacktribe.org/press-releases/",
    "https://www.muckleshoot.nsn.us/press-releases/",
    "https://snoqualmietribe.us/press-releases/",
    "https://www.suquamish.nsn.us/press-releases/",
    "https://jamestowntribe.org/press-releases/",
    "https://www.skokomish.org/press-releases/",
    "https://puyalluptribe-nsn.gov/newsroom/",
    "https://www.nisqually-nsn.gov/news/",
    "https://www.grandronde.org/news/",
    "https://www.ctsi.nsn.us/news/",
    "https://www.coquilletribe.org/news/",
    "https://ctuir.org/news/",
    "https://warmsprings-nsn.gov/news/",
    "https://klamathtribes.org/news/",
    "https://www.karuk.us/index.php/news-events",
    "https://www.yuroktribe.org/news/",
    "https://www.hoopavalley.net/news",
    "https://www.rvit.org/news/",
    "https://big-valley.net/news/",
    "https://www.drycreekrancheria.com/news/",
    "https://gratonrancheria.com/news/",
    "https://middletownrancheria.com/news/",
    "https://www.colusa-nsn.gov/news/",
    "https://www.cowlitz.org/news-media/",
    "https://www.bia.gov/newsroom",
    "https://www.doi.gov/pressreleases",
    "https://www.usa.gov/tribes",
    "https://www.indianaffairs.state.ne.us/resources/national-tribal-resources/",
    "https://www.wliw.org/radio/programs/national-native-news/",
    "https://researchguides.uoregon.edu/nais/news",
    "https://www.nativeweb.org/resources/news_media_television_radio/newspapers_-_native_indigenous/",
    "https://www.cherokeeobserver.org/",
    "https://www.lakotatimes.com/",
    "https://www.rtrpbs.org/native-lens/",
    "https://www.navajohopiobserver.com/",
    "https://newsfromnativecalifornia.com/",
    "https://www.ninilchikvillage.org/",
    "https://www.shoalwaterbay-nsn.gov/",
    "https://timbishashoshone.com/",
    "https://www.oldharbor.org/",
    "https://quileutenation.org/",
    "https://www.bacone.edu/news",
    "https://www.iowatribeofoklahoma.com/news/",
    "https://www.baymills.org/news/",
    "https://www.birchcreektribe.com/",
    "https://www.bishop-paiute.org/news/",
    "https://boisforte.com/news/",
    "https://www.pawneenation.org/news-media/",
    "https://www.semtribe.com/news-media/",
    "https://www.wampanoagtribe.net/news/",
    "https://www.penobscotnation.org/news/",
    "https://www.passamaquoddy.com/news/",
    "https://www.sycuaninstitute.com/news/",
    "https://www.ncai.org/",
    "https://www.nihb.org/news/",
    "https://www.nmai.si.edu/news",
    "https://www.unityinc.org/news",
    "https://www.aifb.com/news",
    "https://www.nativewomensc.org/news",
    "https://www.nativeamericanchamber.com/news"
])))

# File paths
OUTPUT_LIVE_FEEDS_AND_SCRAPE_SOURCES = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\nativekin_live_sources_for_mapping.json"
SOURCE_MAPPING_TEMPLATE_EXCEL = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\source_mapping_template.xlsx"
OUTPUT_ARTICLES_WITH_TRIBE_REGION_FILE = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\nativekin_aggregated_articles_with_tribe_region.json"


# --- Helper Functions (Defined at the top for scope) ---

def find_rss_feed(url):
    """
    Attempts to find the RSS feed URL for a given website URL.
    Checks common RSS patterns and HTML link tags.
    Returns the RSS URL if found and appears valid, None otherwise.
    """
    common_rss_paths = [
        "/feed/", "/rss/", "/rss.xml", "/blog/feed/", "/blog/rss/",
        "/news/feed/", "/atom.xml", "/wp-json/wp/v2/posts?_embed&feed=rss2",
        "/feed/rss/", "/feed/atom/", "/category/news/feed/"
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    for path in common_rss_paths:
        test_url = urljoin(url, path)
        try:
            response = requests.head(test_url, headers=headers, timeout=3) # Use HEAD request for efficiency
            if response.status_code == 200 and ('xml' in response.headers.get('Content-Type', '')):
                # For a HEAD request, we can't check content, so rely on type and status
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
        return bool(feed.entries) and not feed.bozo # Must have entries and no parsing errors
    except Exception:
        return False

def get_feed_info(rss_url, max_entries=10):
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
                'source_url': rss_url,
                'title': title,
                'link': link,
                'published': published,
                'summary': summary.strip()
            })
    except Exception as e:
        # print(f"  An error occurred while getting info from {rss_url}: {e}") # Debugging removed for cleaner output
        pass
    return articles

def scrape_news_articles(base_url, max_articles=5):
    """
    Attempts to scrape recent news articles from a general news page.
    This is a heuristic scraper and might need customization per site based on its HTML structure.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    articles = []
    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for common containers of articles
        containers = soup.find_all(['article', 'div', 'section'], class_=re.compile(r'news-item|post|article|story|entry|hentry|listing-item|card|blog-post', re.I))

        # Fallback to broader search if specific containers are not found
        if not containers:
            main_content_areas = soup.find_all(['main', 'div', 'section'], id=re.compile(r'main-content|content|body|primary', re.I))
            temp_links = []
            for area in main_content_areas:
                # Look for prominent links within these areas that might be articles
                links = area.find_all('a', href=True, text=True)
                for link_tag in links:
                    link_text = link_tag.get_text(strip=True)
                    link_url = urljoin(base_url, link_tag['href'])

                    # Filter out non-article links (e.g., "Read More", "Home", nav links)
                    # and ensure the link text is substantial enough to be a title
                    if len(link_text) > 15 and re.search(r'news|article|story|post|press|media', link_url, re.I) and not re.search(r'category|tag|archive|page|\#', link_url, re.I):
                        temp_links.append({'title': link_text, 'link': link_url})
            # Add these broad links as articles if no structured containers were found
            for item in temp_links[:max_articles]: # Limit articles from broad scrape too
                articles.append({
                    'source_url': base_url,
                    'title': item['title'],
                    'link': item['link'],
                    'published': "Date N/A (Scraped)",
                    'summary': ""
                })
        
        # If containers were found, prioritize extracting from them
        if containers and not articles: # Only process containers if broad scrape didn't already find enough
            for container in containers:
                if len(articles) >= max_articles: break
                
                link_tag = container.find('a', href=True)
                title_tag = container.find(['h1', 'h2', 'h3', 'h4', 'h5'], class_=re.compile(r'title|heading|post-title|entry-title', re.I))
                summary_tag = container.find(['p', 'div'], class_=re.compile(r'summary|description|excerpt|entry-content', re.I))
                
                title = title_tag.get_text(strip=True) if title_tag else (link_tag.get_text(strip=True) if link_tag else None)
                link = urljoin(base_url, link_tag['href']) if link_tag else None
                
                summary = summary_tag.get_text(strip=True) if summary_tag else ""
                summary = BeautifulSoup(summary, 'html.parser').get_text() # Clean HTML tags from summary
                summary = (summary[:500] + '...') if len(summary) > 500 else summary
                
                # Basic validation for scraped links
                if title and link and len(title) > 15 and re.search(r'news|article|story|post|press|media', link.lower()):
                    # Avoid duplicate links if already found in a broader pass
                    if not any(a['link'] == link for a in articles):
                        articles.append({
                            'source_url': base_url,
                            'title': title,
                            'link': link,
                            'published': "Date N/A (Scraped)",
                            'summary': summary.strip()
                        })
        
    except requests.exceptions.RequestException as e:
        # print(f"  Error accessing/scraping {base_url}: {e}") # Keep these logs for debugging if needed
        pass
    except Exception as e:
        # print(f"  An unexpected error occurred during scraping {base_url}: {e}") # Keep these logs for debugging if needed
        pass

    return articles

def load_json_file(filepath, description="data"):
    """Loads JSON data from a specified file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} items from {description} file: {filepath}")
        return data
    except FileNotFoundError:
        return None # Return None if not found, allowing creation
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}. File might be corrupted or empty.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading {description}: {e}")
        return None

def main():
    print("--- Starting Comprehensive Native News Aggregation ---")

    # --- Step 1: Discover Feeds/Scrape Sources and Create Excel Mapping Template ---
    # This phase will run first to generate the Excel template for manual review.
    # It will ONLY proceed to Step 2 if the Excel file exists AND appears to be filled.

    excel_needs_filling = True
    if os.path.exists(SOURCE_MAPPING_TEMPLATE_EXCEL):
        try:
            df_check = pd.read_excel(SOURCE_MAPPING_TEMPLATE_EXCEL, engine='openpyxl')
            if 'Tribe' in df_check.columns and 'Region' in df_check.columns:
                # Check if there are any non-empty, non-NaN values in Tribe/Region columns
                if not (df_check['Tribe'].isnull().all() and df_check['Region'].isnull().all()) and \
                   not ((df_check['Tribe'].astype(str) == '').all() and (df_check['Region'].astype(str) == '').all()):
                    excel_needs_filling = False # Excel has data, proceed to Phase 2
                    print(f"\nDetected existing Excel file '{SOURCE_MAPPING_TEMPLATE_EXCEL}' with filled 'Tribe' and 'Region' columns. Proceeding to Phase 2.")
                else:
                    print(f"\nExcel file '{SOURCE_MAPPING_TEMPLATE_EXCEL}' found but 'Tribe'/'Region' columns are empty. Re-running Phase 1 to generate template.")
            else:
                print(f"\nExcel file '{SOURCE_MAPPING_TEMPLATE_EXCEL}' found but 'Tribe'/'Region' columns are missing. Re-running Phase 1 to generate template.")
        except Exception as e:
            print(f"\nError reading Excel file for check ({e}). Assuming it needs re-generation (Phase 1).")
            excel_needs_filling = True # Error reading, assume needs re-gen

    if excel_needs_filling:
        print("\nPhase 1: Discovering content-rich sources (RSS or Scrape-able) and creating Excel mapping template.")
        
        all_content_yielding_sources_info = [] # Stores info for Excel template

        for i, original_url in enumerate(ALL_POTENTIAL_SOURCES):
            print(f"[{i+1}/{len(ALL_POTENTIAL_SOURCES)}] Processing: {original_url}")
            
            source_info = {
                'Original URL': original_url,
                'Found RSS Feed URL': '',
                'Type of Pull': 'Failed to Pull', # Default status if nothing works
                'Tribe': '', # To be filled manually
                'Region': ''  # To be filled manually
            }
            articles_from_current_source = []

            # Attempt RSS first
            rss_feed_url = find_rss_feed(original_url)
            if rss_feed_url and check_feed_has_entries(rss_feed_url):
                source_info['Found RSS Feed URL'] = rss_feed_url
                source_info['Type of Pull'] = 'RSS'
                articles_from_current_source = get_feed_info(rss_feed_url, max_entries=5) # Get top 5 from RSS for sample
                print(f"  --> Success (RSS). Pulled {len(articles_from_current_source)} sample articles.")
            else:
                # Fallback to direct scraping if RSS is not found or is empty/bad
                articles_from_current_source = scrape_news_articles(original_url, max_articles=3) # Get top 3 from scrape
                if articles_from_current_source:
                    source_info['Type of Pull'] = 'Scrape (fallback)'
                    print(f"  --> Success (Scrape). Pulled {len(articles_from_current_source)} sample articles.")
                else:
                    print(f"  --> Failed to pull articles (No RSS & Scrape yielded nothing).")

            if articles_from_current_source: # Only add to the Excel template if we actually pulled some articles
                all_content_yielding_sources_info.append(source_info)
            
            time.sleep(0.5) # Be polite

        print(f"\nIdentified {len(all_content_yielding_sources_info)} unique sources that yielded content (RSS or Scrape).")
        
        df_template = pd.DataFrame(all_content_yielding_sources_info)
        
        output_dir = os.path.dirname(SOURCE_MAPPING_TEMPLATE_EXCEL)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        df_template.to_excel(SOURCE_MAPPING_TEMPLATE_EXCEL, index=False, engine='openpyxl')
        
        print(f"Excel mapping template created at: {SOURCE_MAPPING_TEMPLATE_EXCEL}")
        print("\n*** ACTION REQUIRED: Please open this Excel file and fill in 'Tribe' and 'Region' for all sources. ***")
        print("    This file only contains sources from which articles were successfully retrieved.")
        print("    Save the Excel file AFTER you fill it out. Then RUN THIS SCRIPT AGAIN for Phase 2.")
        return # Exit after Phase 1, waiting for user input.

    # --- Phase 2: Pull All Articles based on Excel and Enrich/Sort ---
    print("\nPhase 2: Pulling all articles based on your filled Excel mapping and enriching/sorting.")
    
    final_aggregated_articles = []
    
    # Load the completed Excel file to get the mapping
    try:
        df_mapping = pd.read_excel(SOURCE_MAPPING_TEMPLATE_EXCEL, engine='openpyxl')
        # Ensure Tribe and Region columns are treated as strings and fill empty/NaN values with defaults
        df_mapping['Tribe'] = df_mapping['Tribe'].astype(str).replace('nan', 'Unknown Tribe').replace('', 'Unknown Tribe')
        df_mapping['Region'] = df_mapping['Region'].astype(str).replace('nan', 'Unknown Region').replace('', 'Unknown Region')

        source_pull_strategy = {} # Map original_url to its determined RSS/scrape URL, type, tribe, region
        for index, row in df_mapping.iterrows():
            original_url = row['Original URL']
            found_rss_url = row['Found RSS Feed URL']
            pull_type = row['Type of Pull'] # 'RSS' or 'Scrape (fallback)'
            
            # Use found_rss_url if it's RSS, else original_url for scraping
            effective_pull_url = found_rss_url if pull_type == 'RSS' else original_url
            
            source_pull_strategy[original_url] = {
                'tribe': row['Tribe'],
                'region': row['Region'],
                'pull_type': pull_type,
                'effective_pull_url': effective_pull_url
            }
        print(f"Loaded {len(source_pull_strategy)} source mappings and pull strategies from Excel file.")
    except FileNotFoundError:
        print(f"Error: Edited Excel mapping file not found at {SOURCE_MAPPING_TEMPLATE_EXCEL}.")
        print("Please ensure you have filled and saved the Excel file from Phase 1, then run this script again.")
        return
    except Exception as e:
        print(f"Error loading Excel mapping file: {e}")
        return

    # Now, pull articles based on the determined strategy and enrich them
    for i, (original_url, info) in enumerate(source_pull_strategy.items()):
        print(f"[{i+1}/{len(source_pull_strategy)}] Pulling {info['pull_type']} from: {original_url}")
        
        articles_from_source = []
        if info['pull_type'] == 'RSS':
            articles_from_source = get_feed_info(info['effective_pull_url'], max_entries=10) # Pull more entries in final phase
            if not articles_from_source: # If RSS fails in Phase 2 for some reason, try scrape as final fallback
                print(f"  RSS feed {info['effective_pull_url']} failed in Phase 2. Attempting scrape fallback.")
                articles_from_source = scrape_news_articles(original_url, max_articles=5)
        elif info['pull_type'] == 'Scrape (fallback)':
            articles_from_source = scrape_news_articles(info['effective_pull_url'], max_articles=5) # Pull more in final phase
        
        for article in articles_from_source:
            article['tribe'] = info['tribe']
            article['region'] = info['region']
            final_aggregated_articles.append(article)
        
        if not articles_from_source:
            print(f"  No articles pulled from this source ({info['pull_type']}): {original_url}")
        time.sleep(0.5) # Be polite to servers

    print(f"\nPulled a total of {len(final_aggregated_articles)} articles for final output.")

    # Sort articles
    def sort_key(article):
        tribe_key = article.get('tribe', 'Unknown Tribe').lower()
        region_key = article.get('region', 'Unknown Region').lower()
        published_date_str = article.get('published')

        try:
            date_key = datetime.strptime(published_date_str, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            date_key = datetime.min # Places articles with unparseable dates at the beginning of their group for consistency

        return (tribe_key, region_key, date_key)

    final_aggregated_articles.sort(key=sort_key, reverse=True) # Reverse=True for most recent first

    # Save the final aggregated, enriched, and sorted JSON file
    output_dir = os.path.dirname(OUTPUT_ARTICLES_WITH_TRIBE_REGION_FILE)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        with open(OUTPUT_ARTICLES_WITH_TRIBE_REGION_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_aggregated_articles, f, indent=4, ensure_ascii=False)
        print(f"\nSuccessfully saved {len(final_aggregated_articles)} enriched and sorted articles to: {OUTPUT_ARTICLES_WITH_TRIBE_REGION_FILE}")
    except Exception as e:
        print(f"Error saving final JSON file: {e}")

    print("\n--- All Processes Complete ---")

if __name__ == "__main__":
    main()