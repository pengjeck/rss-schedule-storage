import os
import dotenv
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from rss_storage import StorageNews
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

dotenv.load_dotenv(dotenv_path='.env')
app = Flask(__name__)
logging.info("begin to connect google spread sheet")
storage = StorageNews("gs_service_account.json", os.getenv("SHEET_KEY"))
logging.info("end to connect google spread sheet")


def task():
    urls = []
    with open("feeds.txt") as f:
        url = f.readline().strip()
        if len(url) > 4:
            urls.append(url)
    logging.info("feed urls=%s", ','.join(urls))
    storage.storage_to_google_spreadsheet(urls)


@app.route('/')
@app.route('/health')
def health():
    logging.info("health interface")
    return "ok"


scheduler = BackgroundScheduler()
interval = int(os.getenv("INTERVAL_SECONDS"))
logging.info("schedula interval=%d", interval)
scheduler.add_job(task, 'interval', seconds=interval)
scheduler.start()


@app.teardown_appcontext
def treadown(exception=None):
    logging.info("teardown the app context of flask")
    scheduler.shutdown()
