import feedparser
import json
import os

# Resolve path to ../data/nativekin_feeds.json
base_dir = os.path.dirname(__file__)
feed_file = os.path.join(base_dir, '..', 'data', 'nativekin_feeds.json')
output_file = os.path.join(base_dir, '..', 'data', 'nativekin_aggregated_articles.json')

# Load the feed registry
with open(feed_file, 'r') as f:
    tribal_news_sources = json.load(f)

aggregated_articles = []

# Fetch and process each feed
for source in tribal_news_sources:
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

# Save output
with open(output_file, 'w') as f:
    json.dump(aggregated_articles, f, indent=2)

print(f"✅ Aggregated {len(aggregated_articles)} articles from {len(tribal_news_sources)} sources.")
