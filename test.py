import requests
import feedparser

url = "https://www.aljazeera.com/xml/rss/all.xml"
response = requests.get(url, timeout=10)
if response.status_code == 200:
    feed = feedparser.parse(response.content)
    print(feed.feed.link)
