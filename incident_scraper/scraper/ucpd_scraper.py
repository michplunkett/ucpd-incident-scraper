"""Contains code related to scraping UCPD incident reports."""

import logging
import time
from datetime import date, datetime, timedelta

import requests
from lxml import etree, html

from incident_scraper.scraper.headers import Headers
from incident_scraper.utils.constants import TIMEZONE_CHICAGO
from incident_scraper.utils.functions import chicago_midnight_epoch


class UCPDScraper:
    """
    Scrape UCPD incident reports from present day to first day of the year.
    """

    BASE_UCPD_URL = (
        "https://incidentreports.uchicago.edu/incidentReportArchive.php"
    )
    FIRST_INCIDENT_DAY = date(2011, 1, 1)

    def __init__(self, request_delay=0.15):
        self._request_delay = request_delay
        self._headers = {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8,application/"
                "signed-exchange;v=b3;q=0.7"
            ),
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Host": "incidentreports.uchicago.edu",
            "Upgrade-Insecure-Requests": "1",
        }
        self._user_agent_rotator = Headers()

    def scrape_from_beginning_2011(self):
        """Scrape and parse all tables from January 1, 2011, to today."""
        new_url = self._construct_url(self.FIRST_INCIDENT_DAY, self._today())
        return self._get_incidents(new_url)

    def scrape_last_days(self, num_days: int = 3):
        """Scrape and parse all tables from num_days ago to today."""
        today = self._today()
        new_url = self._construct_url(today - timedelta(days=num_days), today)
        return self._get_incidents(new_url)

    @staticmethod
    def _today() -> date:
        return datetime.now(TIMEZONE_CHICAGO).date()

    @classmethod
    def _construct_url(cls, first_day: date, last_day: date) -> str:
        """
        Construct the scraping URL.

        The site wants Chicago-midnight epochs. The end of the range is the
        start of the day after last_day, so that all of last_day is included.
        """
        start_epoch = chicago_midnight_epoch(first_day)
        end_epoch = chicago_midnight_epoch(last_day + timedelta(days=1))

        return (
            f"{cls.BASE_UCPD_URL}?startDate={start_epoch}&endDate={end_epoch}"
            "&offset="
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

        time.sleep(self._request_delay)
        # Change user_agent randomly
        self._headers["User-Agent"] = (
            self._user_agent_rotator.get_random_header()
        )
        r = requests.get(url, headers=self._headers)
        if not r.content.strip():
            raise RuntimeError(
                f"The UCPD site returned an empty page (HTTP {r.status_code}) "
                f"for: {url}"
            )
        response = html.fromstring(r.content)
        container = response.cssselect("thead")
        categories = container[FIRST_INDEX].cssselect("th")
        incidents = response.cssselect("tbody")
        incident_rows = incidents[FIRST_INDEX].cssselect("tr")
        for incident in incident_rows:
            if len(incident) == 1:
                logging.debug(
                    "This incident has a length of 1: "
                    f"{etree.tostring(incident)}"
                )
                continue

            incident_id = incident[INCIDENT_INDEX].text
            if (
                incident_id in ["None", ":"]
                or "No Incident Reports" in incident.text
            ):
                logging.debug(
                    "This incident has an ID of 'None': "
                    f"{etree.tostring(incident)}"
                )
                continue

            incident_dict[incident_id] = {}
            i_dict = {}
            for index in range(len(categories) - 1):
                i_dict[str(categories[index].text).strip()] = str(
                    incident[index].text
                ).strip()

            if [v for v in i_dict.values() if v == "Void"]:
                logging.debug(
                    "This incident contains voided "
                    f"information: {etree.tostring(incident)}"
                )
                continue

            incident_dict[incident_id] = i_dict

        # Track page number, as offset will take you back to zero
        pages = response.cssselect("span.page-link")
        page_numbers = [
            num.strip() for num in pages[FIRST_INDEX].text.split(" / ")
        ]
        return incident_dict, page_numbers[0] == page_numbers[1]

    def _get_incidents(self, new_url: str) -> dict:
        """Get all incidents for a given URL."""
        at_last_page = False
        incidents = {}
        offset = 0

        # Loop until function arrives at last page
        logging.info("Beginning the UCPD Incident scraping process.")
        while not at_last_page:
            rev_dict, at_last_page = self._get_table(new_url + str(offset))
            incidents.update(rev_dict)
            logging.debug(
                f"Scraped {len(incidents)} incidents from the UCPD "
                "Incident page."
            )
            offset += 5
        logging.info("Finished with the UCPD Incident scraping process.")
        return incidents
