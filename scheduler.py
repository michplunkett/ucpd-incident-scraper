"""The python equivalent of a cron file."""
from apscheduler.schedulers.blocking import BlockingScheduler

from incident_scraper.__main__ import update_records

scheduler = BlockingScheduler()


@scheduler.scheduled_job("cron", day_of_week="mon,wed,sat", hour=17, minute=21)
def run_scraper():
    """Run the scraper at the above interval."""
    update_records()


scheduler.start()
