import time
import gspread
import feedparser
from feedparser import FeedParserDict
from newspaper import Article, NewsPool
from newspaper.configuration import Configuration as NewsDownloadConfig
import traceback


def time_guard(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"{func.__name__} took {elapsed_time:.3f} seconds")
        return result
    return wrapper


class News:
    guid: str
    title: str
    describe: str
    content: str
    publishDate: str
    link: str


class SpreadSheet:
    gs = None
    sheets = None

    def __init__(self, service_account_file: str, file_key: str) -> None:
        self.gs = gspread.service_account(filename=service_account_file)
        self.sheets = self.gs.open_by_key(file_key)

    def batch_append(self, news_list: list[News]):
        rows = []
        for news in news_list:
            rows.append([news.guid, news.title, news.describe, news.content,
                        news.publishDate, news.link])
        self.sheets.sheet1.append_rows(rows)

    @time_guard
    def fetch_all_guid(self) -> list[str]:
        return self.fetch_colume_values('guid')

    def fetch_colume_values(self, column="guid"):
        column_map = {
            "guid": 1,
            "title": 2,
            "describe": 3,
            "content": 4,
            "publicDate": 5,
            "link": 6
        }
        if column not in column_map:
            raise KeyError("Columen=" + column + "is not exist.")
        searched = self.sheets.sheet1.col_values(column_map[column])
        output = []
        for item in searched:
            if not item:
                continue
            output.append(item)
        return output


ss = SpreadSheet("gs_service_account.json",
                 "1hXNLUNliBQTwnbd2fMoF6qxCTWmHn2YFF6zRKSUYDuo")


def download_batch_article(urls: list[str]) -> list[Article]:
    news_conf = NewsDownloadConfig()
    news_conf.memoize_articles = False
    news_conf.fetch_images = False
    news_conf.language = 'en'
    news_conf.request_timeout = 7
    news_conf.number_threads = 10

    pool = NewsPool(news_conf)
    articles = [Article(url) for url in urls]
    pool.set(articles)
    pool.join()
    return {article.url: article for article in articles}


def filter_exist_article(feed: FeedParserDict):
    guids = ss.fetch_all_guid()
    print("guids count=", len(guids), " in google spreadsheet")
    return [item.id for item in feed.entries if item.id not in guids]


def update_feed(feed: FeedParserDict):
    not_exist_guids = filter_exist_article(feed)
    filter_feed_entries = [
        item for item in feed.entries if item.id in not_exist_guids]

    urls = [item.link for item in filter_feed_entries]
    articles = download_batch_article(urls)
    news_list = []
    for item in filter_feed_entries:
        if item.link not in articles:
            print("Fail to download artical from url=", item.link)
            continue
        target_article: Article = articles[item.link]
        target_article.parse()

        news = News()
        news.guid = item.id
        news.title = item.title
        news.content = target_article.text
        news.describe = item.summary
        news.link = item.link
        news.publishDate = time.strftime("%Y%m%d", item.published_parsed)
        news_list.append(news)
    ss.batch_append(news_list)


def storage_to_google_spreadsheet():
    feed_urls = []
    with open("feeds.txt") as f:
        url = f.readline().strip()
        if len(url) > 4:
            feed_urls.append(url)
    print("feed urls=", feed_urls)

    for url in feed_urls:
        try:
            feed = feedparser.parse(url)
            print("parsed feed=", url, " contain ",
                  len(feed.entries), "entries")
            update_feed(feed)
        except Exception as e:
            print("meet error when update feed=",
                  url, " of google spreadsheet. error=", e)
            traceback.print_exc()
