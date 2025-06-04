import feedparser

rss_feeds = [
    "https://www.mvskokemedia.com/feed/",
    "https://osagenews.org/feed/",
    "https://www.nativeamericacalling.com/feed/",
    "https://www.nativenews.net/feed/",
    "https://thecirclenews.org/feed/",
    "https://www.lakotatimes.com/rss/",
    "https://ictnews.org/rss/"
]

for url in rss_feeds:
    feed = feedparser.parse(url)
    if feed.bozo:
        print(f"❌ {url} failed: {feed.bozo_exception}")
    else:
        print(f"✅ {url} is OK ({len(feed.entries)} articles)")
