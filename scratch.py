import requests
import feedparser


def read_urls():
    urls = []
    with open("feeds.txt") as f:
        while True:
            line = f.readline()
            if line == "":
                break

            url = line.strip()
            if len(url) > 4:
                urls.append(url)

    return urls


print(read_urls())
