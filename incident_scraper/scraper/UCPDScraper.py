# UCPD Scraper - Class

import pytz
import time
import requests
import lxml.html
from datetime import datetime, time
from urllib.parse import urlparse

# Global Variables


class UCPDScraper:
    def __init__(self, REQUEST_DELAY=0.2):
        self.BASE_UCPD_URL = (
            "https://incidentreports.uchicago.edu/incidentReportArchive.php"
        )
        self.UCPD_URL_REPORT_DATE = self.BASE_UCPD_URL + "?reportDate="
        self.TIMEZONE_CHICAGO = "America/Chicago"
        self.REQUEST_DELAY = REQUEST_DELAY

        # Today's date and time in the Chicago time zone when
        # the scraper is initialized
        self.tz = pytz.timezone(self.TIMEZONE_CHICAGO)
        self.today = datetime.now(self.tz).date()

    @staticmethod
    def get_previous_day_epoch(self, num_days=1):
        """Return epoch time of the previous day at midnight.

        Returns
        -------
        int
            The epoch timestamp of the previous day at midnight.
        """
        # Current date and time in the Chicago time zone

        # Subtract one day from the current date
        previous_day = self.today - datetime.timedelta(days=num_days)
        midnight_utc = self.tz.localize(
            datetime.combine(previous_day, time()), is_dst=None
        )
        return int(midnight_utc.timestamp())

    def construct_url(self, num_days=1):
        """
        Given an initial and a final date, construct the URL for
        posterior scrapping

        Parameters
        ----------
        num_days: int
            The number of days to go back from today's date
        """
        INITIAL_OFFSET = 0

        todays_epoch = self.get_previous_day_epoch(num_days)
        # Difference in number of days between today and the first day of the year
        # This is used to calculate the number of pages to scrape
        days_since_start = (
            self.today - datetime.date(self.today.year, 1, 1)
        ).days
        first_day_epoch = self.get_previous_day_epoch(days_since_start)

        # Construct the URL
        self.constructed_url = f"{self.BASE_UCPD_URL}?startDate={first_day_epoch}&endDate={todays_epoch}&offset={INITIAL_OFFSET}"

    def get_table(self, url: str):
        """Get the table information from that UCPD incident page.

        Parameters
        ----------
        url: str
            A UCPD incident URL for a specific datetime.

        Returns
        -------
            A list of URLs to each park on the page.
        """
        FIRST_INDEX = 0
        INCIDENT_INDEX = 6
        incident_dict = dict()

        print(f"Fetching {url}")
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

    def get_all_tables(self, initial_url: str):
        """Go through all queried tables until we offset back to the first table."""
        page_number = 100000000
        incidents, _ = self.get_table(url=initial_url)

        # Find starting offset
        offset_index = int(initial_url.find("offset="))
        offset = int(initial_url[offset_index + 7 :]) + 5

        # Loop until you offset to the start of query
        while page_number != 1:
            rev_dict, page_number = self.get_table(
                url=self.BASE_UCPD_URL
                + "?startDate=1293861600&endDate=1688274000&offset="
                + str(offset)
            )
            if page_number == 1:
                break
            incidents.update(rev_dict)
            offset += 5
        return str(incidents)
