import time
import gspread
from gspread import Spreadsheet
import feedparser
from feedparser import FeedParserDict
from newspaper import Article, NewsPool
from newspaper.configuration import Configuration as NewsDownloadConfig
import traceback
import requests
import logging
from datetime import date
import calendar
from .filters import DateFilter, ExistFilter, Filter


def time_guard(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"{func.__name__} took {elapsed_time:.3f} seconds")
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


def get_worksheet_name_by_date(target_date: date):
    return target_date.strftime("%Y%m%d")


def create_mouth_sheet(gs_client, month: date, prefix: str = "") -> Spreadsheet:
    _, month_days = calendar.monthrange(month.year, month.month)
    ss_name = prefix + month.strftime("%Y%m")

    ss: Spreadsheet = gs_client.create(ss_name)
    for i in range(month_days):
        the_day = date(month.year, month.month, i + 1)
        ws = ss.add_worksheet(
            get_worksheet_name_by_date(the_day), rows=1, cols=20)
        logging.info(f"Add workshet={ws} to ss={ss.url} of day={the_day}")

    return ss


class DateSpreadSheet:
    COLUMN_MAP = {
        "guid": 1,
        "title": 2,
        "describe": 3,
        "content": 4,
        "publicDate": 5,
        "link": 6
    }

    def __init__(self, ss: Spreadsheet) -> None:
        self.ss: Spreadsheet = ss

    def batch_append(self, news_list: list[News], target_date: date):
        rows = []
        ws_name = get_worksheet_name_by_date(target_date)
        for news in news_list:
            if news.publishDate != ws_name:
                logging.warning(
                    f"News publish date is not same with sheet name. news={news}")
                continue

            rows.append([news.guid, news.title, news.describe, news.content,
                        news.publishDate, news.link])
        self.ss.worksheet(ws_name).append_rows(rows)
        logging.info(
            f"append {len(rows)}news to worksheet={ws_name} of sheet={self.ss.title}")

    @time_guard
    def fetch_all_guid_by_day(self, target_date: date) -> set[str]:
        ws_name = get_worksheet_name_by_date(target_date)
        guids = self.fetch_column_values('guid', ws_name)
        return set(guids)

    def fetch_column_values(self, column: str, ws_name: str):
        if column not in self.COLUMN_MAP:
            raise KeyError("Columen=" + column + "is not exist.")
        searched = self.ss.worksheet(
            ws_name).col_values(self.COLUMN_MAP[column])
        output = []
        for item in searched:
            if not item:
                continue
            output.append(item)
        return output


class StorageNews:
    def __init__(self, ss: Spreadsheet,
                 target_date: date,
                 language='en',
                 request_timeout=7,
                 download_thread_num=10) -> None:
        self.language = language
        self.target_date = target_date
        self.request_timeout = request_timeout
        self.download_thread_num = download_thread_num
        self.ss = DateSpreadSheet(ss)

        self.exist_filter = ExistFilter([])
        self.filter_chain: list[Filter] = [DateFilter(
            target_date), self.exist_filter]

    @time_guard
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

    def exe_filter(self, entry):
        for filter in self.filter_chain:
            if not filter.filter(entry):
                return False
        return True

    def update_feed(self, feed: FeedParserDict):
        filter_feed_entries = [
            item for item in feed.entries if self.exe_filter(item)]
        logging.info(
            f"{len(filter_feed_entries)}, article of feed={feed.feed.link} need to storage in feed.")
        urls = [item.link for item in filter_feed_entries]

        articles = self.download_batch_article(urls)
        logging.info(
            f"{len(articles)} articel of feed={feed.feed.link} had download")
        news_list = []
        for item in filter_feed_entries:
            if item.link not in articles:
                logging.info(f"Fail to download artical from url={item.link}")
                continue
            target_article: Article = articles[item.link]
            target_article.parse()

            news = News.create_from_feed_entry(item, target_article)
            news_list.append(news)
        self.ss.batch_append(news_list, self.target_date)
        self.exist_filter.update_exist_list(
            self.ss.fetch_all_guid_by_day(self.target_date))

    def storage_to_google_spreadsheet(self, feed_urls: list[str]):
        for url in feed_urls:
            try:
                response = requests.get(url, timeout=self.request_timeout)
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    logging.info(
                        f"parsed feed={url} contain {len(feed.entries)} entries")
                    self.update_feed(feed)
                else:
                    logging.warning(f"Failed to fetch the feed={url}")
            except Exception as e:
                logging.warning(
                    f"meet error when update feed={url} of google spreadsheet. error={e}")
                traceback.print_exc()
