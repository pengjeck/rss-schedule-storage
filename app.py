import os
import dotenv
from flask import Flask
import gspread
from gspread import Spreadsheet
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
from src.rss_storage import StorageNews, create_mouth_sheet
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

dotenv.load_dotenv(dotenv_path='.env')
app = Flask(__name__)

index_ss: Spreadsheet = None
GS_SERVICE_ACCOUNT_FILE = "gs_service_account.json"

logging.info("begin to connect google spread sheet")

gs_client = gspread.service_account(GS_SERVICE_ACCOUNT_FILE)
index_ss = gs_client.open_by_url(os.environ.get("INDEX_SHEET_URL"))


def read_urls():
    urls = []
    with open(os.environ.get("RSS_FILE")) as f:
        while True:
            line = f.readline()
            if line == "":
                break

            url = line.strip()
            if len(url) > 4:
                urls.append(url)

    return urls


def task():
    urls = read_urls()
    logging.info("feed urls=%s", ','.join(urls))
    today = date.today()
    records = index_ss.sheet1.get_all_values()
    dates = dict(records)
    today_of_month = today.strftime("%Y%m")

    if today_of_month not in dates:
        logging.info(
            f"spreadsheet of date={today_of_month} is not exist in index, need to create")
        month_ss: Spreadsheet = create_mouth_sheet(
            gs_client=gs_client, month=today, prefix="RSS-")
        append_res = index_ss.sheet1.append_row([today_of_month, month_ss.url])
        dates[today_of_month] = month_ss.url
        logging.info(
            f"create new month sheet={month_ss.url}, append result={append_res}")

    storage_url = dates[today_of_month]
    storage_ss = gs_client.open_by_url(storage_url)

    target_date = today
    target_date_str = os.environ.get("TARGET_DATE")
    if target_date_str and len(target_date_str) > 0:
        target_date = date.fromisoformat(target_date_str)

    logging.info(
        f"create storage of news with storage_ss={storage_ss.url}, target date={target_date}")
    storage = StorageNews(storage_ss, target_date=target_date)
    storage.storage_to_google_spreadsheet(urls)


@app.route('/')
@app.route('/health')
def health():
    logging.info("health interface")
    return "ok"


scheduler = BackgroundScheduler()
interval = int(os.environ.get("INTERVAL_SECONDS"))
logging.info(f"schedula interval={interval}")
scheduler.add_job(task, 'interval', seconds=interval)
scheduler.start()


@app.teardown_appcontext
def treadown(exception=None):
    logging.info("teardown the app context of flask")
    scheduler.shutdown()
