import os
import dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from .storage_task import storage_to_google_spreadsheet

dotenv.load_dotenv()


# Create an instance of scheduler
scheduler = BlockingScheduler()

# Add job to scheduler. Trigger it every 10 seconds
interval = int(os.getenv("INTERVAL_SECONDS"))
scheduler.add_job(storage_to_google_spreadsheet, 'interval', seconds=interval)

# Start the scheduler
try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit) as e:
    print("exception", e)
