import feedparser
import json
import os
from datetime import datetime

feed_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'nativekin_feeds.json')
output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'nativekin_aggregated_articles.json')
log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'rss_log.txt')

# Make logs folder if missing
os.makedirs(os.path.dirname(log_file), exist_ok=True)

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a') as lf:
        lf.write(f"[{timestamp}] {msg}\n")
    print(msg)

# Load feed registry
with open(feed_file, 'r') as f:
    tribal_news_sources = json.load(f)

aggregated_articles = []

# Parse feeds
for source in tribal_news_sources:
    log(f"🔍 Fetching: {source['name']} ({source['rss']})")
    feed = feedparser.parse(source['rss'])
    entry_count = len(feed.entries)
    log(f"→ {entry_count} entries found.")
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

# Save only if there are new articles
if aggregated_articles:
    with open(output_file, 'w') as f:
        json.dump(aggregated_articles, f, indent=2)
    log(f"✅ Saved {len(aggregated_articles)} articles to {output_file}")
else:
    log("⚠️ No articles aggregated. JSON not updated.")
