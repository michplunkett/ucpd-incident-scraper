"""Contains the Incident model and all of its associated information."""

from datetime import datetime

import pytz
from google.cloud.ndb import DateProperty, GeoPtProperty, Model, StringProperty

from incident_scraper.utils.constants import TIMEZONE_CHICAGO, UCPD_DATE_FORMAT


class Incident(Model):
    """Standard data structure for recovered UCPD incidents."""

    id = StringProperty(indexed=True)
    ucpd_id = StringProperty(indexed=True)
    incident = StringProperty(indexed=True)
    reported = StringProperty()
    reported_date = DateProperty(indexed=True)
    occurred = StringProperty()
    comments = StringProperty()
    disposition = StringProperty()
    location = StringProperty()
    validated_address = StringProperty()
    validated_location = GeoPtProperty()


def set_validated_location(scrape_response: dict, census_response: str):
    """Set the validated locations properties."""
    if not census_response:
        return False

    scrape_response["ValidatedAddress"] = census_response[0]
    scrape_response["ValidatedLatitude"] = census_response[1]
    scrape_response["ValidatedLongitude"] = census_response[2]

    return True


def date_str_to_iso_format(date_str: str):
    """Take a date string and return in it a localized ISO format."""
    return (
        datetime.strptime(date_str, UCPD_DATE_FORMAT)
        .astimezone(pytz.timezone(TIMEZONE_CHICAGO))
        .isoformat()
    )


def date_str_to_date_format(date_str: str):
    """Take a date string and return in it a localized date format."""
    return datetime.strptime(date_str, UCPD_DATE_FORMAT).date()
