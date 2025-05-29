import os
import json
import feedparser
from datetime import datetime

# Set up directories
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, '..', 'data')
log_dir = os.path.join(script_dir, '..', 'logs')

# File paths
feed_file = os.path.join(data_dir, 'nativekin_feeds.json')
output_file = os.path.join(data_dir, 'nativekin_aggregated_articles.json')
log_file = os.path.join(log_dir, 'rss_log.txt')

# Ensure log directory exists
os.makedirs(log_dir, exist_ok=True)

# Load tribal RSS feed definitions
with open(feed_file, 'r', encoding='utf-8') as f:
    tribal_news_sources = json.load(f)

aggregated_articles = []
log_entries = []

# Parse each RSS feed
for source in tribal_news_sources:
    try:
        feed = feedparser.parse(source['rss'])
        if feed.bozo:
            log_entries.append(f"[{datetime.now()}] Error parsing {source['name']} feed: {feed.bozo_exception}")
            continue
        for entry in feed.entries[:5]:  # Limit to top 5 per feed
            aggregated_articles.append({
                'title': entry.get('title', 'No Title'),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'summary': entry.get('summary', '')[:300],
                'source': source['name'],
                'tribe': source['tribe'],
                'national': source['national']
            })
        log_entries.append(f"[{datetime.now()}] Parsed {len(feed.entries[:5])} entries from {source['name']}")
    except Exception as e:
        log_entries.append(f"[{datetime.now()}] Exception reading {source['name']}: {str(e)}")

# Save output
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(aggregated_articles, f, indent=2)

# Write logs
with open(log_file, 'a', encoding='utf-8') as logf:
    for entry in log_entries:
        logf.write(entry + '\n')

print(f"✅ Aggregated {len(aggregated_articles)} articles from {len(tribal_news_sources)} sources.")
