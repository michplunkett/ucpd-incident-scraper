"""Contains code related to scraping UCPD incident reports."""
import time
from datetime import datetime
from datetime import time as dt_time
from datetime import timedelta

import lxml.html
import pytz
import requests
from utils.constants import TIMEZONE_CHICAGO


class UCPDScraper:
    """Scrape UCPD incident reports from present day to first day of the year."""

    BASE_UCPD_URL = (
        "https://incidentreports.uchicago.edu/incidentReportArchive.php"
    )
    UCPD_URL_REPORT_DATE = BASE_UCPD_URL + "?reportDate="

    def __init__(self, request_delay=0.2):
        self.request_delay = request_delay

        # Today's date and time in the Chicago time zone when
        # the scraper is initialized
        self.tz = pytz.timezone(TIMEZONE_CHICAGO)
        self.today = datetime.now(self.tz).date()

        print(f"Today's date: {self.today}")
        print("Constructing URL...")
        self.construct_url()

    def get_previous_day_epoch(self, num_days=1):
        """Return epoch time of a previous day at midnight.

        Given the number of days to subtract from the current date,
        return the epoch time of that day at midnight.
        """
        # Subtract one day from the current date
        today = datetime.now(self.tz).date()
        previous_day = today - timedelta(days=num_days)
        midnight_utc = self.tz.localize(
            datetime.combine(previous_day, dt_time()), is_dst=None
        )
        return int(midnight_utc.timestamp())

    def construct_url(self):
        """
        Construct the url to scrape from.

        Constructs the url to scrape from by getting the epochs of the
        present day and the first day of the current year.
        """
        INITIAL_OFFSET = 0

        self.todays_epoch = self.get_previous_day_epoch(num_days=0)
        # Difference in number of days between today and the first day of the year
        # This is used to calculate the number of pages to scrape
        days_since_start = (
            self.today - datetime(self.today.year, 1, 1).date()
        ).days
        self.first_day_epoch = self.get_previous_day_epoch(days_since_start)

        # Construct the URL
        self.constructed_url = f"{self.BASE_UCPD_URL}?startDate={self.first_day_epoch}&endDate={self.todays_epoch}&offset={INITIAL_OFFSET}"

    def get_table(self, url: str):
        """
        Get the table information from that UCPD incident page.

        Scrapes the table from the given url and returns a dictionary.
        """
        FIRST_INDEX = 0
        INCIDENT_INDEX = 6
        incident_dict ={}

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
            incident_id = str(incident[INCIDENT_INDEX].text)
            if incident_id == "None":
                continue
            incident_dict[incident_id] = dict()
            for index in range(len(categories) - 1):
                incident_dict[incident_id][
                    str(categories[index].text)
                ] = incident[index].text

        # Track page number, as offset will take you back to zero
        pages = response.cssselect("span.page-link")
        slash_index = pages[FIRST_INDEX].text.find("/")
        page_number = (
            int(pages[FIRST_INDEX].text[: slash_index - 1])
            if slash_index != -1
            else 0
        )
        return incident_dict, page_number

    def get_all_tables(self):
        """Go through all queried tables until we offset back to the first table."""
        page_number = 100000000
        incidents, _ = self.get_table(url=self.constructed_url)

        # Find starting offset
        offset_index = int(self.constructed_url.find("offset="))
        offset = int(self.constructed_url[offset_index + 7 :]) + 5

        # Loop until you offset to the start of query
        while page_number != 1:
            new_url = f"{self.BASE_UCPD_URL}?startDate={self.first_day_epoch}&endDate={self.todays_epoch}&offset={offset}"
            rev_dict, page_number = self.get_table(new_url)
            if page_number == 1:
                break
            incidents.update(rev_dict)
            offset += 5
        return str(incidents)
