from feedparser import FeedParserDict
from datetime import date
import time


class Filter:
    def filter(self, feed_entry: FeedParserDict):
        """
        过滤 feed 条目。

        Args:
            feed_entry (FeedParserDict): feed 条目。

        Returns:
            bool: 如果需要过滤掉该 feed 条目，则返回 False，否则返回 True。
        """
        return False


class ExistFilter(Filter):
    def __init__(self, exist_guids: set) -> None:
        self.exist_guids = exist_guids

    def update_exist_list(self, exist_guids: set):
        self.exist_guids = exist_guids

    def filter(self, feed_entry: FeedParserDict):
        """
        过滤掉指定 feed_entry，如果 feed_entry 的 id 不在 feed_entry 中则返回 True，否则返回 False。

        Args:
            feed_entry (FeedParserDict): 需要过滤的 feed_entry 对象。

        Returns:
            bool: 如果 feed_entry 的 id 不在 feed_entry 中则返回 True，否则返回 False。

        """
        return feed_entry.id not in feed_entry


class DateFilter(Filter):
    def __init__(self, target_date: date) -> None:
        self.target_date = target_date.strftime("%Y%m%d")

    def filter(self, feed_entry: FeedParserDict):
        """
        根据目标日期过滤RSS订阅源条目

        Args:
            feed_entry (FeedParserDict): RSS订阅源条目，包含条目信息

        Returns:
            bool: 如果RSS订阅源条目的发布日期等于目标日期，则返回True，否则返回False

        """
        return self.target_date == time.strftime("%Y%m%d", feed_entry.published_parsed)
