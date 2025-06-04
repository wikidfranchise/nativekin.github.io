import requests
import feedparser
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

# List of tribal news website URLs to check
# This list now contains only the confirmed working feeds from your last run,
# plus a significant number of new "Indian News Outlets" to expand our search.
NEWS_SOURCES = [
    # --- Previously Working Feeds (from your last run's summary) ---
    "https://ictnews.org/",
    "https://www.indianz.com/",
    "https://www.nativenewsonline.net/",
    "https://www.nativeamericacalling.com/",
    "https://www.hcn.org/issues/indigenous-affairs",
    "https://thecirclenews.org/",
    "https://osagenews.org/",
    "https://www.mvskokemedia.com/",
    "https://www.spokanetribe.com/news/",
    "https://nativenewsonline.net/", # Duplicate but confirms it works
    "https://www.powwows.com/news/",
    "https://www.narf.org/news/",
    "https://www.culturalsurvival.org/news",
    "https://www.meskwaki.org/news-events/",
    "https://www.cowlitz.org/news-media/",
    "https://ltbbodawa-nsn.gov/news/",
    "https://www.yakama.com/news-media/",

    # --- NEW "Indian News Outlets" and Related Organizations (20+ additions) ---
    # Focusing on news organizations, media centers, and larger advocacy groups with news sections
    "https://api.rp-feed.org/feed", # Respected news aggregation for Indigenous issues (Native American Journalists Association)
    "https://www.wbur.org/radioboston/tags/native-americans", # WBUR (NPR) - Native American topic page
    "https://www.kpbs.org/tags/native-americans", # KPBS (NPR) - Native American topic page
    "https://www.opb.org/news/topic/native-americans/", # Oregon Public Broadcasting - Native American section
    "https://www.kxci.org/category/news/", # KXCI Community Radio - Indigenous news
    "https://www.koahnic.org/news/", # Koahnic Broadcasting Corporation (National Native News producer)
    "https://www.firstnations.org/news/", # First Nations Development Institute - news section
    "https://news.azpm.org/s/2959-native-american/", # Arizona Public Media - Native American news
    "https://www.culturalsurvival.org/news/", # Already listed, but a good example of this category
    "https://www.fncil.com/blog", # First Nations Community HealthSource - blog/news
    "https://www.nativephilanthropy.org/news/", # Native Americans in Philanthropy - news
    "https://www.pechanga.com/news/", # Pechanga Band of Luiseño Indians - News (prominent Southern California tribe)
    "https://www.tribalnetmedia.com/news/", # TribalNet - focuses on tech/broadband for tribes, but has news
    "https://ncaied.org/news/", # National Center for American Indian Enterprise Development - news
    "https://naja.com/news/", # Native American Journalists Association (NAJA) - their own news/updates
    "https://www.ndncollective.org/news/", # NDN Collective - Indigenous advocacy news
    "https://www.honordignityrespect.org/news/", # Honor the Earth - Indigenous environmental justice news
    "https://www.seventhgen.org/news/", # Seventh Generation Fund for Indigenous Peoples - news
    "https://www.nawi.org/news-updates/", # National American Indian Women's Business Council - news
    "https://www.niea.org/newsroom/", # National Indian Education Association - newsroom
    "https://www.ncai.org/news/press-releases", # National Congress of American Indians (NCAI) - Press Releases (might have RSS)
    "https://www.doi.gov/bureaus/bia/newsroom", # Bureau of Indian Affairs (BIA) - Newsroom (official government news)
    "https://www.bia.gov/newsroom", # Alternative BIA newsroom URL
    "https://www.fnai.org/news/", # First Nations Academy of Indian Art - news
    "https://www.aihec.org/news/", # American Indian Higher Education Consortium (AIHEC) - news
    "https://www.navajotimes.com/news/", # Direct link to Navajo Times news section, hoping for a feed
    "https://gricnews.org/", # Gila River Indian Community News (a direct news publication)
    "https://www.wmat.nsn.us/news.html", # White Mountain Apache Tribe news (re-added as it's a specific news section)
    "https://www.quinai.com/news/", # Quinault Indian Nation news
    "https://www.northernarapaho.com/news-announcements/", # Northern Arapaho Tribe news
    "https://www.choctawnation.com/news/", # Choctaw Nation news
    "https://chickasaw.net/News/", # Chickasaw Nation news
    "https://www.oneidanation.org/news-events/", # Oneida Nation of Wisconsin news
    "https://saulttribe.com/news-media", # Sault Ste. Marie Tribe news
    "https://www.mohican.com/news/", # Stockbridge-Munsee Community News (adjusted to direct news section)
    "https://www.gtbindians.org/news-media/", # Grand Traverse Band news
    "https://www.lacduflambeau.com/news/", # Lac du Flambeau news
    "https://www.menominee-nsn.gov/news-media-events", # Menominee Indian Tribe news
    "https://www.ho-chunk.com/news/", # Ho-Chunk Nation news
    "https://www.tulaliptribes-nsn.gov/Home/News", # Tulalip Tribes news
    "https://www.grandronde.org/news/", # Confederated Tribes of Grand Ronde news
    "https://www.critt.org/news-archive/", # Colorado River Indian Tribes news
]

def find_rss_feed(url):
    """
    Attempts to find the RSS feed URL for a given website URL.
    Checks common RSS patterns and HTML link tags.
    """
    common_rss_paths = [
        "/feed/",
        "/rss/",
        "/rss.xml",
        "/blog/feed/",
        "/blog/rss/",
        "/news/feed/",
        "/atom.xml",
        "/wp-json/wp/v2/posts?_embed&feed=rss2", # Common WordPress REST API feed
        "/feed/rss/", # Another common WordPress path
        "/feed/atom/", # Another common Atom path
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # 1. Try common RSS paths
        for path in common_rss_paths:
            test_url = urljoin(url, path) # Use urljoin for robust path joining
            try:
                response = requests.get(test_url, headers=headers, timeout=5)
                # Check for XML content type or XML/RSS/Atom-like start tags in content
                if response.status_code == 200 and (
                    'xml' in response.headers.get('Content-Type', '') or
                    '<rss' in response.text.lower() or
                    '<feed' in response.text.lower()
                ):
                    print(f"  Found common path RSS: {test_url}")
                    return test_url
            except requests.exceptions.RequestException:
                pass # Continue to next path or method

        # 2. Parse HTML for RSS link tags
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for <link rel="alternate" type="application/rss+xml">
        # or <link rel="alternate" type="application/atom+xml">
        feed_link = soup.find('link', rel='alternate', type=['application/rss+xml', 'application/atom+xml'])
        if feed_link and 'href' in feed_link.attrs:
            rss_url = feed_link['href']
            # Handle relative URLs
            if not rss_url.startswith(('http://', 'https://')):
                rss_url = urljoin(url, rss_url)
            print(f"  Found HTML link tag RSS: {rss_url}")
            return rss_url

    except requests.exceptions.RequestException as e:
        print(f"  Error accessing {url}: {e}")
    except Exception as e:
        print(f"  An unexpected error occurred while finding RSS for {url}: {e}")

    return None

def check_rss_feed(rss_url):
    """
    Checks if an RSS feed URL is valid, readable, and contains entries.
    Returns True if valid and has entries, False otherwise.
    """
    try:
        feed = feedparser.parse(rss_url)
        if feed.bozo: # Check if there were parsing errors
            if hasattr(feed.bozo_exception, 'getMessage'):
                print(f"    Validation Error (Bozo): {feed.bozo_exception.getMessage()}")
            else:
                print(f"    Validation Error (Bozo): {feed.bozo_exception}")
            return False
        if not feed.entries:
            print("    Valid RSS feed found, but NO ENTRIES. Excluding per request.")
            return False # Exclude if no entries found
        else:
            print(f"    Valid RSS feed. Found {len(feed.entries)} entries.")
            return True
    except Exception as e:
        print(f"    Error parsing RSS feed {rss_url}: {e}")
        return False

def main():
    working_rss_feeds = []
    print("Starting RSS feed discovery and validation...\n")

    for i, url in enumerate(NEWS_SOURCES):
        print(f"[{i+1}/{len(NEWS_SOURCES)}] Checking: {url}")
        rss_url = find_rss_feed(url)

        if rss_url:
            print(f"  Potential RSS feed found: {rss_url}")
            if check_rss_feed(rss_url):
                working_rss_feeds.append((url, rss_url))
            else:
                print(f"  RSS feed {rss_url} failed validation or had no entries.")
        else:
            print("  No RSS feed found for this URL using common methods.")
        print("-" * 50)
        time.sleep(1) # Be polite to websites, wait 1 second between requests

    print("\n--- Summary of CURRENT Working RSS Feeds ---")
    print(f"Total working feeds found: {len(working_rss_feeds)}\n")
    if working_rss_feeds:
        for original_url, rss_feed_url in working_rss_feeds:
            print(f"Original: {original_url}\nRSS Feed: {rss_feed_url}\n")
    else:
        print("No current working RSS feeds were found from the provided list.")

if __name__ == "__main__":
    main()