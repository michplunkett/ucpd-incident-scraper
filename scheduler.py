"""The python equivalent of a cron file."""
from apscheduler.schedulers.blocking import BlockingScheduler

from incident_scraper.__main__ import update_records


scheduler = BlockingScheduler()


# The time below is in UTC
@scheduler.scheduled_job(
    trigger="cron", day_of_week="mon,tue,wed,thu,fri,sat", hour=14
)
def run_scraper():
    """Run the scraper at the above interval."""
    update_records()


scheduler.start()
