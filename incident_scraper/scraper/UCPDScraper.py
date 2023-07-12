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
