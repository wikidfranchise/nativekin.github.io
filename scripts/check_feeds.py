import feedparser

feeds = [
    {"name": "Mvskoke Media", "url": "https://www.mvskokemedia.com/feed/"},
    {"name": "Osage News", "url": "https://osagenews.org/feed/"},
    {"name": "Native America Calling", "url": "https://www.nativeamericacalling.com/feed/"},
    {"name": "National Native News", "url": "https://www.nativenews.net/feed/"},
    {"name": "The Circle News", "url": "https://thecirclenews.org/feed/"},
    {"name": "Lakota Times", "url": "https://www.lakotatimes.com/rss/"},
    {"name": "ICT News", "url": "https://ictnews.org/rss/"},
    {"name": "Indian Country Echo", "url": "https://www.indiancountryecho.org/feed/"},
    {"name": "Indian Gaming", "url": "https://indiangaming.com/feed/"},
    {"name": "News From Native California", "url": "https://newsfromnativecalifornia.com/feed/"},
    {"name": "Native Sun News Today", "url": "https://www.nativesunnews.today/rss/"}, 
    {"name": "Arizona Indian News", "url": "https://www.aianews.com/rss/"}, 
    {"name": "The Southern Ute Drum", "url": "https://www.sudrum.com/feed/"},
    {"name": "Tribal Business News", "url": "https://tribalbusinessnews.com/rss"},
    {"name": "Native News from Oregon", "url": "https://www.opb.org/rss/topic/native-american/"},
    {"name": "Wabanaki Alliance", "url": "https://wabanakialliance.com/feed/"},
    {"name": "Indian Country Media Network", "url": "https://indiancountrymedianetwork.com/feed/"},
    {"name": "Native Voice One", "url": "https://nv1.org/feed/"},
    {"name": "Alaska Native News", "url": "https://alaska-native-news.com/feed/"},
    {"name": "First Nations Drum", "url": "https://www.firstnationsdrum.com/feed/"}
]

for feed in feeds:
    d = feedparser.parse(feed["url"])
    if d.bozo:
        print(f"❌ {feed['name']} ({feed['url']}) failed: {d.bozo_exception}")
    else:
        print(f"✅ {feed['name']} ({feed['url']}) is OK ({len(d.entries)} articles)")
