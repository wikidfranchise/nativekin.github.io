import feedparser
import json
import os
from datetime import datetime

# Define paths
base_dir = os.path.dirname(__file__)
data_dir = os.path.join(base_dir, '..', 'data')
log_dir = os.path.join(base_dir, '..', 'logs')
feed_file = os.path.join(data_dir, 'nativekin_feeds.json')
output_file = os.path.join(data_dir, 'nativekin_aggregated_articles.json')
log_file = os.path.join(log_dir, 'rss_log.txt')

# Ensure the logs directory exists
os.makedirs(log_dir, exist_ok=True)

# Load feed registry
try:
    with open(feed_file, 'r', encoding='utf-8') as f:
        tribal_news_sources = json.load(f)
except Exception as e:
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(f"[{datetime.now()}] ERROR reading feed list: {e}\n")
    raise SystemExit(f"Error loading feed list: {e}")

aggregated_articles = []
feed_errors = []

# Parse feeds
for source in tribal_news_sources:
    try:
        feed = feedparser.parse(source['rss'])
        for entry in feed.entries[:5]:
            aggregated_articles.append({
                'title': entry.get('title', 'No Title'),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'summary': entry.get('summary', '')[:300],
                'source': source['name'],
                'tribe': source['tribe'],
                'national': source['national']
            })
    except Exception as e:
        feed_errors.append((source['name'], str(e)))

# Save output
try:
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(aggregated_articles, f, indent=2, ensure_ascii=False)
except Exception as e:
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(f"[{datetime.now()}] ERROR writing output JSON: {e}\n")
    raise SystemExit(f"Error saving aggregated articles: {e}")

# Log result
with open(log_file, 'a', encoding='utf-8') as log:
    log.write(f"[{datetime.now()}] Aggregated {len(aggregated_articles)} articles from {len(tribal_news_sources)} sources\n")
    if feed_errors:
        log.write(f"   Feed errors ({len(feed_errors)}):\n")
        for name, err in feed_errors:
            log.write(f"     - {name}: {err}\n")
