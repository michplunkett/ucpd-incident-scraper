"""Contains code relating to the Google Cloud Platform Datastore service."""
import json
import os
from datetime import date, datetime

from google.cloud.ndb import Client, GeoPt, put_multi

from incident_scraper.models.incident import Incident
from incident_scraper.utils.constants import UCPD_MDY_KEY_DATE_FORMAT


def get_incident(ucpd_id: str):
    """Get Incident from datastore."""
    incident = Incident.get_by_id(ucpd_id)
    if incident:
        return incident
    else:
        return None


class GoogleNBD:
    """Create the client and access GCP NBD functionality."""

    ENTITY_TYPE = "Incident"
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
    CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    def __init__(self):
        if self.CREDENTIALS.endswith(".json"):
            self.client = Client(self.PROJECT_ID)
        else:
            self.client = Client(
                credentials=json.loads(self.CREDENTIALS),
                project=self.PROJECT_ID,
            )

    @staticmethod
    def _create_incident_from_dict(incident: dict):
        """Convert an incident dict to a Incident Model."""
        return Incident(
            id=f"{incident['UCPD_ID']}_{incident['ReportedDate']}",
            ucpd_id=incident["UCPD_ID"],
            incident=incident["Incident"],
            reported=incident["Reported"].isoformat(),
            reported_date=incident["ReportedDate"],
            occurred=incident["Occurred"],
            comments=incident["Comments / Nature of Fire"],
            disposition=incident["Disposition"],
            location=incident["Location"],
            validated_address=incident["ValidatedAddress"],
            validated_location=GeoPt(
                incident["ValidatedLongitude"],
                incident["ValidatedLatitude"],
            ),
        )

    def add_incident(self, incident: dict):
        """Add Incident to datastore."""
        with self.client.context():
            nbd_incident = self._create_incident_from_dict(incident)
            nbd_incident.put(incident)

    def add_incidents(self, incidents: [Incident]):
        """Add Incidents to datastore in bulk."""
        with self.client.context():
            incident_keys = []
            for i in incidents:
                nbd_incident = self._create_incident_from_dict(i)
                incident_keys.append(nbd_incident)
            put_multi(incident_keys)

    def get_latest_date(self) -> date:
        """Get latest incident date."""
        with self.client.context():
            query = Incident.query().order(-Incident.reported_date).fetch(1)
            if query:
                return datetime.strptime(
                    query[0].reported_date, UCPD_MDY_KEY_DATE_FORMAT
                ).date()
            else:
                return datetime.now().date()

    def remove_incident(self, ucpd_id: str):
        """Remove incident from datastore."""
        with self.client.context():
            incident = Incident(ucpd_id=ucpd_id)
            incident.delete()
