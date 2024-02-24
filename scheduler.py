"""The python equivalent of a cron file."""
from apscheduler.schedulers.blocking import BlockingScheduler

from incident_scraper.__main__ import (
    download_and_upload_records,
    update_records,
)


scheduler = BlockingScheduler()


# The time below is in UTC
@scheduler.scheduled_job(trigger="cron", day_of_week="mon-sat", hour=16)
def run_scraper():
    """Run the scraper at the above interval."""
    update_records()


@scheduler.scheduled_job(trigger="cron", day_of_week="sun", hour=0)
def export_to_maroon_google_drive():
    """Export the incidents to Google Drive at the above interval."""
    download_and_upload_records()


scheduler.start()
