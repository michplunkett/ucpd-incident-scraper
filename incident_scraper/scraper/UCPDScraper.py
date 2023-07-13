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

    @staticmethod
    def previous_day_midnight_epoch_time(self):
        """Return epoch time of the previous day at midnight.

        Returns
        -------
        int
            The epoch timestamp of the previous day at midnight.
        """
        # Current date and time in the Chicago time zone
        tz = pytz.timezone(self.TIMEZONE_CHICAGO)
        today = datetime.now(tz).date()
        # Subtract one day from the current date
        yesterday = today - datetime.timedelta(days=1)
        midnight_utc = tz.localize(
            datetime.combine(yesterday, time()), is_dst=None
        )
        return int(midnight_utc.timestamp())

    def get_table(url: str):
        """Get the table information from that UCPD incident page.

        Parameters
        ----------
        url: str
            A UCPD incident URL for a specific datetime.

        Returns
        -------
            A list of URLs to each park on the page.
        """
        incident_dict = dict()
        response = page_grab(url)
        container = response.cssselect("thead")
        categories = container[0].cssselect("th")
        incidents = response.cssselect("tbody")
        incident_rows = incidents[0].cssselect("tr")
        for incident in incident_rows:
            if len(incident) == 1:
                continue
            incident_id = str(incident[6].text)
            if incident_id == "None":
                continue
            incident_dict[incident_id] = dict()
            for i in range(len(categories) - 1):
                incident_dict[incident_id][str(categories[i].text)] = incident[
                    i
                ].text

        # Track page number, as offset will take you back to zero
        pages = response.cssselect("span.page-link")
        slash_index = pages[0].text.find("/")
        page_number = (
            int(pages[0].text[: slash_index - 1]) if slash_index != -1 else 0
        )
        return incident_dict, page_number
