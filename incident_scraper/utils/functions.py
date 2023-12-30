from datetime import datetime
from typing import Optional

from incident_scraper.utils.constants import (
    INCIDENT_KEY_REPORTED,
    UCPD_DATE_FORMATS,
)


def parse_scraped_incident_timestamp(i: dict) -> Optional[str]:
    result = None

    for time_format in UCPD_DATE_FORMATS:
        try:
            result = datetime.strptime(i[INCIDENT_KEY_REPORTED], time_format)
        except ValueError:
            continue
        # If a date is successfully parsed, break from the loop.
        break

    return result
