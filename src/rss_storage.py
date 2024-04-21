import time
import gspread
import feedparser
from feedparser import FeedParserDict
from newspaper import Article, NewsPool
from newspaper.configuration import Configuration as NewsDownloadConfig
import traceback
import requests


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
    def __init__(self, feed_entry: FeedParserDict, article: Article):
        self.guid = feed_entry.id
        self.title = feed_entry.title
        self.describe = feed_entry.summary
        self.content = article.text
        self.link = feed_entry.link
        self.publishDate = time.strftime("%Y%m%d", feed_entry.published_parsed)

    @staticmethod
    def create_from_feed_entry(feed_entry: FeedParserDict, article: Article):
        return News(feed_entry, article)


class SpreadSheet:
    gs = None
    sheets = None

    COLUMN_MAP = {
        "guid": 1,
        "title": 2,
        "describe": 3,
        "content": 4,
        "publicDate": 5,
        "link": 6
    }

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
        return self.fetch_column_values('guid')

    def fetch_column_values(self, column="guid"):
        if column not in self.COLUMN_MAP:
            raise KeyError("Columen=" + column + "is not exist.")
        searched = self.sheets.sheet1.col_values(self.COLUMN_MAP[column])
        output = []
        for item in searched:
            if not item:
                continue
            output.append(item)
        return output


class StorageNews:
    def __init__(self, google_service_account_file="", sheet_key="",
                 language='en',
                 request_timeout=7,
                 download_thread_num=10) -> None:
        self.language = language
        self.request_timeout = request_timeout
        self.download_thread_num = download_thread_num
        self.ss = SpreadSheet(google_service_account_file, sheet_key)

    def download_batch_article(self, urls: list[str]) -> dict[str, Article]:
        news_conf = NewsDownloadConfig()
        news_conf.memoize_articles = False
        news_conf.fetch_images = False
        news_conf.language = self.language
        news_conf.request_timeout = self.request_timeout
        news_conf.number_threads = self.download_thread_num

        pool = NewsPool(news_conf)
        articles = [Article(url) for url in urls]
        pool.set(articles)
        pool.join()
        return {article.url: article for article in articles}

    def filter_exist_article(self, feed: FeedParserDict):
        guids = self.ss.fetch_all_guid()
        print("guids count=", len(guids), " in google spreadsheet")
        return [item.id for item in feed.entries if item.id not in guids]

    def update_feed(self, feed: FeedParserDict):
        not_exist_guids = self.filter_exist_article(feed)
        filter_feed_entries = [
            item for item in feed.entries if item.id in not_exist_guids]
        print(len(filter_feed_entries), " article of feed",
              feed.feed.link, " need to storage in feed")
        urls = [item.link for item in filter_feed_entries]
        articles = self.download_batch_article(urls)
        print(len(articles), " articel of feed",
              feed.feed.link, " downloaded.")
        news_list = []
        for item in filter_feed_entries:
            if item.link not in articles:
                print("Fail to download artical from url=", item.link)
                continue
            target_article: Article = articles[item.link]
            target_article.parse()

            news = News.create_from_feed_entry(item, target_article)
            news_list.append(news)
        self.ss.batch_append(news_list)

    def storage_to_google_spreadsheet(self, feed_urls: list[str]):
        for url in feed_urls:
            try:
                response = requests.get(url, timeout=self.request_timeout)
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    print("parsed feed=", url, " contain ",
                          len(feed.entries), "entries")
                    self.update_feed(feed)
                else:
                    print("Failed to fetch the feed=", url)
            except Exception as e:
                print("meet error when update feed=",
                      url, " of google spreadsheet. error=", e)
                traceback.print_exc()
