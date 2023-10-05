"""Contains code related to scraping UCPD incident reports."""
import logging
import time
from datetime import datetime, timedelta

import requests
from lxml import etree, html

from incident_scraper.scraper.headers import Headers
from incident_scraper.utils.constants import (
    TIMEZONE_CHICAGO,
    UCPD_MDY_DATE_FORMAT,
)


class UCPDScraper:
    """
    Scrape UCPD incident reports from present day to first day of the year.
    """

    BASE_UCPD_URL = (
        "https://incidentreports.uchicago.edu/incidentReportArchive.php"
    )

    def __init__(self, request_delay=0.2):
        self.request_delay = request_delay
        self.headers = {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8,application/"
                "signed-exchange;v=b3;q=0.7"
            ),
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Host": "incidentreports.uchicago.edu",
            "Upgrade-Insecure-Requests": "1",
        }
        self.user_agent_rotator = Headers()

    def scrape_from_beginning_2023(self):
        """Scrape and parse all tables from January 1, 2023, to today."""
        new_url = self._construct_url(year_beginning=True)
        return self._get_incidents(new_url)

    def scrape_last_days(self, num_days: int = 3):
        """Scrape and parse all tables from num_days ago to today."""
        new_url = self._construct_url(num_days=num_days)
        return self._get_incidents(new_url)

    def _construct_url(self, num_days: int = 0, year_beginning: bool = False):
        """
        Construct the scraping URL.

        Constructs the URL to scrape from by getting the epochs of the present
        day and the first day of the current year.
        """
        today = datetime.now(TIMEZONE_CHICAGO).date()
        today_str = today.strftime(UCPD_MDY_DATE_FORMAT)

        previous_datetime = (
            datetime(2023, 1, 1).date()
            if year_beginning
            else today - timedelta(days=num_days)
        )
        previous_date_str = previous_datetime.strftime(UCPD_MDY_DATE_FORMAT)

        return (
            f"{self.BASE_UCPD_URL}?startDate={previous_date_str}&endDate="
            f"{today_str}&offset="
        )

    def _get_table(self, url: str):
        """
        Get the table information from that UCPD incident page.

        Scrapes the table from the given url and returns a dictionary and a
        boolean stating if it scraped the last page.
        """
        FIRST_INDEX = 0
        INCIDENT_INDEX = 6
        incident_dict = {}

        logging.debug(f"Fetching {url}")
        time.sleep(self.request_delay)
        # Change user_agent randomly
        self.headers["User-Agent"] = self.user_agent_rotator.get_random_header()
        r = requests.get(url, headers=self.headers)
        response = html.fromstring(r.content)
        container = response.cssselect("thead")
        categories = container[FIRST_INDEX].cssselect("th")
        incidents = response.cssselect("tbody")
        incident_rows = incidents[FIRST_INDEX].cssselect("tr")
        for incident in incident_rows:
            if len(incident) == 1:
                logging.error(
                    "This incident had a length of 1: "
                    f"{etree.tostring(incident)}"
                )
                continue

            incident_id = incident[INCIDENT_INDEX].text
            if (
                incident_id in ["None", ":"]
                or "No Incident Reports" in incident.text
            ):
                logging.error(
                    "This incident had an ID of 'None': "
                    f"{etree.tostring(incident)}"
                )
                continue

            incident_dict[incident_id] = {}
            for index in range(len(categories) - 1):
                incident_dict[incident_id][
                    str(categories[index].text).strip()
                ] = str(incident[index].text).strip()

        # Track page number, as offset will take you back to zero
        pages = response.cssselect("span.page-link")
        page_numbers = [
            num.strip() for num in pages[FIRST_INDEX].text.split(" / ")
        ]
        return incident_dict, page_numbers[0] == page_numbers[1]

    def _get_incidents(self, new_url: str):
        """Get all incidents for a given URL."""
        at_last_page = False
        incidents = {}
        offset = 0

        # Loop until function arrives at last page
        logging.info("Beginning the UCPD Incident scraping process.")
        while not at_last_page:
            rev_dict, at_last_page = self._get_table(new_url + str(offset))
            incidents.update(rev_dict)
            offset += 5
        logging.info("Finished with the UCPD Incident scraping process.")
        return incidents
