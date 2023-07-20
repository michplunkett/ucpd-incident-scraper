"""Contains the Incident model and all of its associated information."""

from datetime import datetime
from typing import Any

import pytz
from jsonic import Serializable

from incident_scraper.utils.constants import TIMEZONE_CHICAGO, UCPD_DATE_FORMAT


class Incident(Serializable):
    """Standard data structure for recovered UCPD incidents."""

    ucpd_id: str
    incident: str
    location: str
    reported: str
    reported_date: Any
    occurred: str
    comments: str
    disposition: str
    validated_location: str
    validated_latitude: float
    validate_longitude: float

    def __init__(self, gcp_response: dict, scrape_response: dict):
        super().__init__()
        if gcp_response:
            self.ucpd_id = gcp_response["ucpd_id"]
            self.incident = gcp_response["incident"]
            self.location = gcp_response["location"]
            self.reported = gcp_response["reported"]
            self.reported_date = datetime.strptime(
                gcp_response["reported_date"], UCPD_DATE_FORMAT
            ).date()
            self.occurred = gcp_response["occurred"]
            self.comments = gcp_response["comments"]
            self.disposition = gcp_response["disposition"]
        elif scrape_response:
            self.ucpd_id = scrape_response["UCPD_ID"]
            self.incident = scrape_response["Incident"]
            self.location = scrape_response["Location"]
            self.reported = scrape_response["Reported"]
            self.reported_date = scrape_response["Reported"]
            self.occurred = scrape_response["Occurred"]
            self.comments = scrape_response["Comments / Nature of Fire"]
            self.disposition = scrape_response["Disposition"]

        self.validated_location = gcp_response["validated_location"]
        self.validated_latitude = float(gcp_response["validated_latitude"])
        self.validate_longitude = float(gcp_response["validate_longitude"])

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

    def get_parsed_location(self):
        """Parse UCPD sourced location for validation."""
        return self.location.split(" (")[0]

    def set_validated_location(self, census_response: str):
        """Set the validated locations properties."""
        if not census_response:
            return False

        self.validated_location = census_response[0]
        self.validated_latitude = census_response[1]
        self.validate_longitude = census_response[2]

        return True
