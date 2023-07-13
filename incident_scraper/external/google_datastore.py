"""Contains code relating to the Google Cloud Platform Datastore service."""
import os
from datetime import datetime

from google.cloud.datastore import Client
from jsonic import Serializable, deserialize, serialize

from incident_scraper.utils.constants import TIMEZONE_CHICAGO

UCPD_DATE_FORMAT = "%x %-I:%M %p"
UCPD_DOY_DATE_FORMAT = "%x"


class Incident(Serializable):
    """Standard data structure for recovered UCPD incidents."""

    def __init__(
        self,
        ucpd_id: str,
        incident: str,
        location: str,
        reported: str,
        occurred: str,
        comments: str,
        disposition: str,
    ):
        super().__init__()
        self.ucpd_id = ucpd_id
        # incident example: "Information / Theft"
        self.incident = incident.split(" / ")
        # location example: "8675309 NSW. Texas (DDR)"
        self.location = location
        self.reported = self._date_str_to_iso_format(reported)
        self.reported_date = self._date_str_to_datastore_format(reported)
        self.occurred = self._date_str_to_iso_format(occurred)
        self.comments = comments
        self.disposition = disposition
        self.validated_location = None

    @staticmethod
    def _date_str_to_iso_format(date_str: str):
        """Take a date and return in it a localized ISO format."""
        return (
            datetime.strptime(date_str, UCPD_DATE_FORMAT)
            .astimezone(TIMEZONE_CHICAGO)
            .isoformat()
        )

    @staticmethod
    def _date_str_to_datastore_format(date_str: str):
        """Take a date and return it as a localized MM/DD/YYYY format."""
        return (
            datetime.strptime(date_str, UCPD_DATE_FORMAT)
            .astimezone(TIMEZONE_CHICAGO)
            .strftime(UCPD_DOY_DATE_FORMAT)
        )

    def get_parsed_location(self):
        """Parse UCPD sourced location for validation."""
        return self.location.split(" (")[0]

    def set_validated_location(self, census_location: str):
        """Set the `validated_location` property."""
        self.validated_location = census_location


class GoogleDatastore:
    """Create the client and access GCP datastore functionality."""

    ENTITY_TYPE = "Incident"
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

    def __init__(self):
        self.client = Client(self.PROJECT_ID)

    def add_incident(self, incident: Incident):
        """Add incident to datastore."""
        complete_key = self.client.key(self.ENTITY_TYPE, incident.ucpd_id)
        gcp_incident = self.client.Entity(key=complete_key)
        gcp_incident.update(serialize(incident))
        self.client.put(gcp_incident)

    def get_incident(self, ucpd_id: str):
        """Get incident from datastore."""
        incident = self.client.get(self.client.key(self.ENTITY_TYPE, ucpd_id))
        if incident:
            return deserialize(incident)
        else:
            return None

    def remove_incident(self, ucpd_id: str):
        """Remove incident from datastore."""
        self.client.delete(self.client.key(self.ENTITY_TYPE, ucpd_id))
