"""Contains constants that are used throughout the application."""

# Date/Time Constants
TIMEZONE_CHICAGO = "America/Chicago"
UCPD_DATE_FORMAT = "%x %I:%M %p"
UCPD_DOY_DATE_FORMAT = "%x"
UCPD_MDY_DATE_FORMAT = "%m/%d/%Y"

# File Constants
FILE_OPEN_MODE_READ = "r"

# Scraping Constants
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
    "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Host": "incidentreports.uchicago.edu",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ("
    "HTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
}
