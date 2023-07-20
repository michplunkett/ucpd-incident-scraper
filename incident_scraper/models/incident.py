"""Contains the Incident model and all of its associated information."""

from datetime import datetime

import pytz
from google.cloud.ndb import (
    DateTimeProperty,
    FloatProperty,
    Model,
    StringProperty,
)

from incident_scraper.utils.constants import TIMEZONE_CHICAGO, UCPD_DATE_FORMAT


class Incident(Model):
    """Standard data structure for recovered UCPD incidents."""

    def __init__(self, gcp_response: dict = None, scrape_response: dict = None):
        super().__init__()
        if gcp_response:
            self.ucpd_id = StringProperty(gcp_response["ucpd_id"])
            self.incident = StringProperty(gcp_response["incident"])
            self.location = StringProperty(gcp_response["location"])
            self.reported = StringProperty(gcp_response["reported"])
            self.reported_date = DateTimeProperty(
                datetime.strptime(
                    gcp_response["reported_date"], UCPD_DATE_FORMAT
                )
            )
            self.occurred = StringProperty(gcp_response["occurred"])
            self.comments = StringProperty(gcp_response["comments"])
            self.disposition = StringProperty(gcp_response["disposition"])
            self.validated_location = StringProperty(
                gcp_response["validated_location"]
            )
            self.validated_latitude = FloatProperty(
                float(gcp_response["validated_latitude"])
            )
            self.validate_longitude = FloatProperty(
                float(gcp_response["validate_longitude"])
            )
        elif scrape_response:
            self.ucpd_id = StringProperty(scrape_response["UCPD_ID"])
            self.incident = StringProperty(scrape_response["Incident"])
            self.location = StringProperty(scrape_response["Location"])
            self.reported = StringProperty(scrape_response["Reported"])
            self.reported_date = DateTimeProperty(
                datetime.strptime(scrape_response["Reported"], UCPD_DATE_FORMAT)
            )
            self.occurred = StringProperty(scrape_response["Occurred"])
            self.comments = StringProperty(
                scrape_response["Comments / Nature of Fire"]
            )
            self.disposition = StringProperty(scrape_response["Disposition"])
            self.validated_location = StringProperty(
                scrape_response["validated_location"]
            )
            self.validated_latitude = FloatProperty(
                float(scrape_response["validated_latitude"])
            )
            self.validate_longitude = FloatProperty(
                float(scrape_response["validate_longitude"])
            )

    def _date_str_to_iso_format(self, date_str: str):
        """Take a date and return in it a localized ISO format."""
        return (
            datetime.strptime(date_str, self.UCPD_DATE_FORMAT)
            .astimezone(pytz.timezone(TIMEZONE_CHICAGO))
            .isoformat()
        )

    def _date_str_to_datastore_format(self, date_str: str):
        """Take a date and return it as a localized MM/DD/YYYY format."""
        return (
            datetime.strptime(date_str, self.UCPD_DATE_FORMAT)
            .astimezone(pytz.timezone(TIMEZONE_CHICAGO))
            .strftime(self.UCPD_DOY_DATE_FORMAT)
        )

    def set_validated_location(self, census_response: str):
        """Set the validated locations properties."""
        if not census_response:
            return False

        self.validated_location = census_response[0]
        self.validated_latitude = census_response[1]
        self.validate_longitude = census_response[2]

        return True
