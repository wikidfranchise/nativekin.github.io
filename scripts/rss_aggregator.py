
import feedparser
import json
from datetime import datetime

# Load the tribal news sources
with open('nativekin_feeds.json', 'r') as f:
    tribal_news_sources = json.load(f)

aggregated_articles = []

for source in tribal_news_sources:
    feed = feedparser.parse(source['rss'])
    for entry in feed.entries[:5]:  # Only pull latest 5 entries per source
        aggregated_articles.append({
            'title': entry.get('title', 'No Title'),
            'link': entry.get('link', ''),
            'published': entry.get('published', ''),
            'summary': entry.get('summary', '')[:300],
            'source': source['name'],
            'tribe': source['tribe'],
            'national': source['national']
        })

# Write the aggregated data
with open('nativekin_aggregated_articles.json', 'w') as f:
    json.dump(aggregated_articles, f, indent=2)

print(f"Aggregated {len(aggregated_articles)} articles from {len(tribal_news_sources)} sources.")
