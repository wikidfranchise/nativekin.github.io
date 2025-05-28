import feedparser
import json
import os

# Locate the feeds JSON file in the parent data/ directory
feed_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'nativekin_feeds.json')
with open(feed_file, 'r') as f:
    tribal_news_sources = json.load(f)

aggregated_articles = []

for source in tribal_news_sources:
    feed = feedparser.parse(source['rss'])
    for entry in feed.entries[:5]:  # Only fetch latest 5 per source
        aggregated_articles.append({
            'title': entry.get('title', 'No Title'),
            'link': entry.get('link', ''),
            'published': entry.get('published', ''),
            'summary': entry.get('summary', '')[:300],
            'source': source['name'],
            'tribe': source['tribe'],
            'national': source['national']
        })

# Save the aggregated result in the data/ directory
output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'nativekin_aggregated_articles.json')
with open(output_file, 'w') as f:
    json.dump(aggregated_articles, f, indent=2)

print(f"✅ Aggregated {len(aggregated_articles)} articles from {len(tribal_news_sources)} sources.")
