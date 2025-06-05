import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

base_url = "https://nativeamericans.einnews.com"

headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(base_url, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

rss_links = []

# Look for <a href="..."> containing 'rss'
for tag in soup.find_all("a", href=True):
    href = tag['href']
    if "rss" in href.lower():
        full_url = urljoin(base_url, href)
        rss_links.append(full_url)

# Remove duplicates and print
rss_links = sorted(set(rss_links))
print("FOUND RSS FEEDS:")
for link in rss_links:
    print(link)
