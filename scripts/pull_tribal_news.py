import requests
import feedparser
import time
from datetime import datetime
from bs4 import BeautifulSoup
import json
import os # Import the os module for path manipulation

# --- Confirmed Working RSS Feeds ---
# This list is now directly populated with the RSS feed URLs that were found to be working
# and contain entries.
WORKING_RSS_FEEDS = [
    "https://ictnews.org/feed/",
    "https://www.indianz.com/news/feed/",
    "https://www.nativenewsonline.net/feed/",
    "https://www.nativeamericacalling.com/feed/",
    "https://www.hcn.org/feed/",
    "https://thecirclenews.org/feed/",
    "https://osagenews.org/feed/",
    "https://www.mvskokemedia.com/feed/",
    "https://www.spokanetribe.com/feed/",
    "https://nativenewsonline.net/feed/",
    "https://www.powwows.com/feed/",
    "https://www.narf.org/feed/",
    "https://www.culturalsurvival.org/rss/",
    "https://www.meskwaki.org/feed/",
    "https://www.cowlitz.org/rss.xml",
    "https://ltbbodawa-nsn.gov/feed/",
    "https://www.yakama.com/feed/",
    "https://www.wbur.org/feed/",
    "https://www.kxci.org/feed/",
    "https://www.koahnic.org/rss.xml",
    "https://www.bia.gov/rss.xml",
]

def get_feed_info(rss_url, max_entries=10):
    """
    Parses an RSS feed and extracts information from its entries.
    Args:
        rss_url (str): The URL of the RSS feed.
        max_entries (int): Maximum number of entries to retrieve per feed.
    Returns:
        list: A list of dictionaries, each representing an article with 'title', 'link', 'published', 'summary'.
    """
    articles = []
    try:
        feed = feedparser.parse(rss_url)

        if feed.bozo:
            # print(f"  Error parsing feed {rss_url}: {feed.bozo_exception}") # Removed for cleaner output to console
            return []

        for i, entry in enumerate(feed.entries):
            if i >= max_entries:
                break # Limit to max_entries

            title = entry.get('title', 'No Title')
            link = entry.get('link', 'No Link')

            published_parsed = entry.get('published_parsed')
            if published_parsed:
                try:
                    published = datetime(*published_parsed[:6]).strftime('%Y-%m-%d %H:%M:%S')
                except TypeError:
                    published = entry.get('published', 'No Date')
            else:
                published = entry.get('published', 'No Date')

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
        print(f"  An error occurred while getting info from {rss_url}: {e}")

    return articles

def main():
    all_articles = []
    print("Starting to pull information from confirmed RSS feeds...\n")

    for i, feed_url in enumerate(WORKING_RSS_FEEDS):
        print(f"[{i+1}/{len(WORKING_RSS_FEEDS)}] Processing feed: {feed_url}")
        articles_from_feed = get_feed_info(feed_url, max_entries=10)
        if articles_from_feed:
            all_articles.extend(articles_from_feed)
        print("-" * 50)
        time.sleep(1)

    print("\n--- Saving Consolidated Article Information ---")

    all_articles.sort(key=lambda x: datetime.strptime(x['published'], '%Y-%m-%d %H:%M:%S') if x['published'] != 'No Date' else datetime.min, reverse=True)

    # Define the exact output file path as requested
    output_filepath = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\nativekin_aggregated_articles.json"

    # Ensure the directory exists before writing the file
    output_dir = os.path.dirname(output_filepath)
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")
        except OSError as e:
            print(f"Error creating directory {output_dir}: {e}")
            print("Cannot save file. Please check permissions or path.")
            return # Exit if directory cannot be created

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved {len(all_articles)} articles to {output_filepath}")
    except Exception as e:
        print(f"Error saving articles to JSON file at {output_filepath}: {e}")

    # Optional: Print to console for quick review
    print("\n--- Console Preview (Top 10 Articles) ---")
    if all_articles:
        for j, article in enumerate(all_articles[:10]):
            print(f"Article {j+1}:")
            print(f"  Source: {article['source_url']}")
            print(f"  Title: {article['title']}")
            print(f"  Link: {article['link']}")
            print(f"  Published: {article['published']}")
            print(f"  Summary: {article['summary']}")
            print("-" * 30)
        if len(all_articles) > 10:
            print(f"\n...and {len(all_articles) - 10} more articles saved to {output_filepath}")
    else:
        print("No articles were retrieved.")

if __name__ == "__main__":
    main()