"""Contains code related to scraping UCPD incident reports."""
import time
from datetime import datetime
from datetime import time as dt_time
from datetime import timedelta

import lxml.html
import pytz
import requests

from incident_scraper.utils.constants import TIMEZONE_CHICAGO


class UCPDScraper:
    """Scrape UCPD incident reports from present day to first day of the year."""

    BASE_UCPD_URL = (
        "https://incidentreports.uchicago.edu/incidentReportArchive.php"
    )
    TZ = pytz.timezone(TIMEZONE_CHICAGO)

    def __init__(self, request_delay=0.2):
        self.request_delay = request_delay
        self.today = datetime.now(self.TZ).date()
        self.base_url = self._construct_url()

    def scrape_from_beginning_2023(self):
        """Scrape and parse all tables from January 1, 2023 to today."""
        pass

    def scrape_last_three_days(self):
        """Scrape and parse all tables from three days ago to today."""
        pass

    def scrape_last_five_days(self):
        """Scrape and parse all tables from five days ago to today."""
        pass

    def scrape_last_ten_days(self):
        """Scrape and parse all tables from ten days ago to today."""
        pass

    def _get_previous_day_epoch(self, num_days=1):
        """Return epoch time of a previous day at midnight.

        Given the number of days to subtract from the current date, return the epoch
        time of that day at midnight.
        """
        # Subtract one day from the current date
        previous_day = self.today - timedelta(days=num_days)
        previous_day_midnight = self.TZ.localize(
            datetime.combine(previous_day, dt_time()), is_dst=None
        )
        return int(previous_day_midnight.timestamp())

    def _construct_url(self):
        """
        Construct the url to scrape from.

        Constructs the url to scrape from by getting the epochs of the present day and
        the first day of the current year.
        """
        current_day = self._get_previous_day_epoch(num_days=0)
        # Difference in number of days between today and the first day of the year
        # This is used to calculate the number of pages to scrape
        days_since_start = (
            self.today - datetime(self.today.year, 1, 1).date()
        ).days
        first_day_of_year = self._get_previous_day_epoch(days_since_start)

        print(f"Today's date: {self.today}")
        print("Constructing URL...")
        return (
            f"{self.BASE_UCPD_URL}?startDate={first_day_of_year}&endDate="
            f"{current_day}&offset="
        )

    def _get_table(self, url: str):
        """
        Get the table information from that UCPD incident page.

        Scrapes the table from the given url and returns a dictionary and a boolean
        stating if it scraped the last page..
        """
        FIRST_INDEX = 0
        INCIDENT_INDEX = 6
        incident_dict = dict()

        print(f"Fetching {url}")
        time.sleep(self.request_delay)
        r = requests.get(url)
        response = lxml.html.fromstring(r.content)
        container = response.cssselect("thead")
        categories = container[FIRST_INDEX].cssselect("th")
        incidents = response.cssselect("tbody")
        incident_rows = incidents[FIRST_INDEX].cssselect("tr")
        for incident in incident_rows:
            if len(incident) == 1:
                continue
            incident_id = incident[INCIDENT_INDEX].text.strip()
            if incident_id == "None":
                continue
            incident_dict[incident_id] = dict()
            for index in range(len(categories) - 1):
                incident_dict[incident_id][
                    str(categories[index].text.strip())
                ] = incident[index].text.strip()

        # Track page number, as offset will take you back to zero
        pages = response.cssselect("span.page-link")
        page_numbers = pages[FIRST_INDEX].text.split(" / ")
        return incident_dict, page_numbers[0] == page_numbers[1]

    def get_all_tables(self):
        """Go through all queried tables until we offset back to the first table."""
        at_last_page = False
        incidents = dict()
        offset = 0

        # Loop until function arrives at last page
        while not at_last_page:
            rev_dict, at_last_page = self._get_table(
                self.base_url + str(offset)
            )
            incidents.update(rev_dict)
            offset += 5
        return str(incidents)
