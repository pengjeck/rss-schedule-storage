import os
import dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from .storage_task import StorageRSS

dotenv.load_dotenv()


def task():
    urls = []
    with open("feeds.txt") as f:
        url = f.readline().strip()
        if len(url) > 4:
            urls.append(url)
    storage = StorageRSS(urls, "gs_service_account.json",
                         os.getenv("SHEET_KEY"))
    storage.storage_to_google_spreadsheet()


# Create an instance of scheduler
scheduler = BlockingScheduler()

# Add job to scheduler. Trigger it every 10 seconds
interval = int(os.getenv("INTERVAL_SECONDS"))
scheduler.add_job(task, 'interval', seconds=interval)

# Start the scheduler
try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit) as e:
    print("exception", e)
