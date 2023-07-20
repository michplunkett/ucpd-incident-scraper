"""Contains code related to scraping UCPD incident reports."""
import time
from datetime import datetime, timedelta

import lxml.html
import pytz
import requests

from incident_scraper.scraper.headers import Headers
from incident_scraper.utils.constants import HEADERS, TIMEZONE_CHICAGO


class UCPDScraper:
    """Scrape UCPD incident reports from present day to first day of the year."""

    BASE_UCPD_URL = (
        "https://incidentreports.uchicago.edu/incidentReportArchive.php"
    )
    TZ = pytz.timezone(TIMEZONE_CHICAGO)
    UCPD_MDY_DATE_FORMAT = "%m/%d/%Y"

    def __init__(self, request_delay=0.2):
        self.request_delay = request_delay
        self.today = datetime.now(self.TZ).date()
        self.today_str = self.today.strftime(self.UCPD_MDY_DATE_FORMAT)
        self.base_url = self._construct_url(0)
        self.headers = HEADERS.copy()
        self.user_agent_rotator = Headers()

    def scrape_from_beginning_2023(self):
        """Scrape and parse all tables from January 1, 2023, to today."""
        new_url = self._construct_url(year_beginning=True)
        self._get_incidents(new_url)

    def scrape_last_three_days(self):
        """Scrape and parse all tables from three days ago to today."""
        new_url = self._construct_url(num_days=3)
        self._get_incidents(new_url)

    def scrape_last_five_days(self):
        """Scrape and parse all tables from five days ago to today."""
        new_url = self._construct_url(num_days=5)
        self._get_incidents(new_url)

    def scrape_last_ten_days(self):
        """Scrape and parse all tables from ten days ago to today."""
        new_url = self._construct_url(num_days=10)
        self._get_incidents(new_url)

    def _construct_url(self, num_days=0, year_beginning=False):
        """
        Construct the scraping URL.

        Constructs the URL to scrape from by getting the epochs of the present day and
        the first day of the current year.
        """
        previous_datetime = (
            datetime(2023, 1, 1).date()
            if year_beginning
            else self.today - timedelta(days=num_days)
        )
        previous_date_str = previous_datetime.strftime(
            self.UCPD_MDY_DATE_FORMAT
        )

        print(f"Today's date: {self.today}")
        print("Constructing URL...")
        return (
            f"{self.BASE_UCPD_URL}?startDate={previous_date_str}&endDate="
            f"{self.today_str}&offset="
        )

    def _get_table(self, url: str):
        """
        Get the table information from that UCPD incident page.

        Scrapes the table from the given url and returns a dictionary and a boolean
        stating if it scraped the last page.
        """
        FIRST_INDEX = 0
        INCIDENT_INDEX = 6
        incident_dict = dict()

        print(f"Fetching {url}")
        time.sleep(self.request_delay)
        # Change user_agent randomly
        self.headers["User-Agent"] = self.user_agent_rotator.get_random_header()
        r = requests.get(url, headers=self.headers)
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
        return incident_dict, page_numbers[0].strip() == page_numbers[1].strip()

    def _get_incidents(self, new_url: str):
        """Get all incidents for a given URL."""
        at_last_page = False
        incidents = dict()
        offset = 0

        # Loop until function arrives at last page
        while not at_last_page:
            rev_dict, at_last_page = self._get_table(new_url + str(offset))
            incidents.update(rev_dict)
            offset += 5
        return str(incidents)
