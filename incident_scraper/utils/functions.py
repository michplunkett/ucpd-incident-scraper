import re
from datetime import datetime
from typing import Optional

from incident_scraper.utils.constants import (
    INCIDENT_KEY_REPORTED,
    UCPD_DATE_FORMATS,
)


def parse_scraped_incident_timestamp(i: dict) -> Optional[str]:
    result = None

    # Compensate for date input irregularities
    i[INCIDENT_KEY_REPORTED] = re.sub(
        r"\s{0}AM", " AM", i[INCIDENT_KEY_REPORTED]
    )
    i[INCIDENT_KEY_REPORTED] = re.sub(
        r"\s{0}PM", " PM", i[INCIDENT_KEY_REPORTED]
    )
    i[INCIDENT_KEY_REPORTED] = re.sub(r"\s{2,}", " ", i[INCIDENT_KEY_REPORTED])
    i[INCIDENT_KEY_REPORTED] = (
        i[INCIDENT_KEY_REPORTED]
        .replace("//", "/")
        .replace("!", "1")
        .replace(" at ", " ")
        .replace(":PM", " PM")
        .replace(":AM", " AM")
        .replace(": PM", " PM")
        .replace(": AM", " AM")
    )

    for time_format in UCPD_DATE_FORMATS:
        try:
            result = datetime.strptime(i[INCIDENT_KEY_REPORTED], time_format)
        except ValueError:
            continue
        # If a date is successfully parsed, break from the loop.
        break

    return result
