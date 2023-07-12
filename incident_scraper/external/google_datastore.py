"""Contains code relating to the Google Cloud Platform Datastore service."""
import os
from datetime import datetime

from google.cloud.datastore import Client

from incident_scraper.utils.constants import TIMEZONE_CHICAGO

DATASTORE_DATE_KEY_FORMAT = "%x"
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
UCPD_DATE_FORMAT = "%x %-I:%M %p"


class Incident:
    """Standard data structure for recovered UCPD incidents."""

    def __init__(
        self,
        id: str,
        incident: str,
        location: str,
        reported: str,
        occurred: str,
        comments: str,
        disposition: str,
    ):
        self.id = id
        # incident example: "Information / Theft"
        self.incident = incident.split(" / ")
        self.location = location
        self.reported = (
            datetime.strptime(reported, UCPD_DATE_FORMAT)
            .astimezone(TIMEZONE_CHICAGO)
            .isoformat()
        )
        self.occurred = (
            datetime.strptime(occurred, UCPD_DATE_FORMAT)
            .astimezone(TIMEZONE_CHICAGO)
            .isoformat()
        )
        self.comments = comments
        self.disposition = disposition


class Datastore:
    """Create the client and access GCP datastore functionality."""

    def __init__(self):
        self.client = Client(PROJECT_ID)

    def _add_date_incident_list(self):
        """Add date key to Datastore if it does not already exist."""
        pass

    def _does_incident_exist(self):
        """Check if incident is in datastore list for its respective date."""
        pass

    def add_incident(self):
        """Add incident to datastore."""
        pass

    def remove_incident(self):
        """Remove incident from datastore."""
        pass
