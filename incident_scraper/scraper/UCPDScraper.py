# UCPD Scraper - Class

import pytz
import time
import requests
import lxml.html
from datetime import datetime, time
from urllib.parse import urlparse

# Global Variables
BASE_UCPD_URL = "https://incidentreports.uchicago.edu/incidentReportArchive.php"
UCPD_URL_REPORT_DATE = BASE_UCPD_URL + "?reportDate="

TIMEZONE_CHICAGO = "America/Chicago"
