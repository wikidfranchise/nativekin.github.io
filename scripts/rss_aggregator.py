import feedparser
import json
import os
from datetime import datetime

# File paths
base_dir = os.path.dirname(__file__)
feed_file = os.path.join(base_dir, '..', 'data', 'nativekin_feeds.json')
output_file = os.path.join(base_dir, '..', 'data', 'nativekin_aggregated_articles.json')
log_file = os.path.join(base_dir, '..', 'logs', 'rss_log.txt')

# Ensure logs dir exists
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Load feed registry
with open(feed_file, 'r') as f:
    tribal_news_sources = json.load(f)

aggregated_articles = []
log_lines = [f"\n[{datetime.utcnow().isoformat()} UTC] Feed aggregation run\n"]

# Parse feeds
for source in tribal_news_sources:
    feed = feedparser.parse(source['rss'])
    entry_count = len(feed.entries)
    log_lines.append(f"- {source['name']} ({source['tribe']}): {entry_count} entries")

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

# Save aggregated data
with open(output_file, 'w') as f:
    json.dump(aggregated_articles, f, indent=2)

# Save log file
with open(log_file, 'a') as f:
    f.write('\n'.join(log_lines) + '\n')

print(f"✅ Aggregated {len(aggregated_articles)} articles from {len(tribal_news_sources)} sources.")
