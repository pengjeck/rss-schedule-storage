import os
import dotenv
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from rss_storage import StorageNews

dotenv.load_dotenv(dotenv_path='.env')
app = Flask(__name__)
print("begin to connect google spread sheet")
storage = StorageNews("gs_service_account.json", os.getenv("SHEET_KEY"))
print("end to connect google spread sheet")


def task():
    urls = []
    with open("feeds.txt") as f:
        url = f.readline().strip()
        if len(url) > 4:
            urls.append(url)
    print("feed urls=", urls)
    storage.storage_to_google_spreadsheet(urls)


@app.route('/')
@app.route('/health')
def health():
    return "ok"


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    interval = int(os.getenv("INTERVAL_SECONDS"))
    print("schedula interval=", interval)
    scheduler.add_job(task, 'interval', seconds=interval)
    scheduler.start()

    try:
        app.run()
    finally:
        scheduler.shutdown()
