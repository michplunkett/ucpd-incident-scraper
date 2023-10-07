"""Contains code relating to the Google Cloud Platform Datastore service."""
import csv
import json
import logging
from datetime import date, datetime

from google.cloud.datastore.helpers import GeoPoint
from google.cloud.ndb import Client, GeoPt, put_multi
from google.oauth2 import service_account

from incident_scraper.models.incident import Incident
from incident_scraper.utils.constants import (
    ENV_GCP_CREDENTIALS,
    ENV_GCP_PROJECT_ID,
    FILE_OPEN_MODE_WRITE,
    FILE_TYPE_JSON,
    INCIDENT_KEY_ADDRESS,
    INCIDENT_KEY_COMMENTS,
    INCIDENT_KEY_ID,
    INCIDENT_KEY_LATITUDE,
    INCIDENT_KEY_LOCATION,
    INCIDENT_KEY_LONGITUDE,
    INCIDENT_KEY_REPORTED,
    INCIDENT_KEY_REPORTED_DATE,
    UCPD_MDY_KEY_DATE_FORMAT,
)


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

    def __init__(self):
        if ENV_GCP_CREDENTIALS.endswith(FILE_TYPE_JSON):
            self.client = Client(ENV_GCP_PROJECT_ID)
        else:
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(ENV_GCP_CREDENTIALS)
            )
            self.client = Client(
                credentials=credentials,
                project=ENV_GCP_PROJECT_ID,
            )

    @staticmethod
    def _create_incident_from_dict(incident: dict):
        """Convert an incident dict to a Incident Model."""
        return Incident(
            id=f"{incident[INCIDENT_KEY_ID]}_{incident[INCIDENT_KEY_REPORTED_DATE]}",
            ucpd_id=incident[INCIDENT_KEY_ID],
            incident=incident["Incident"],
            reported=incident[INCIDENT_KEY_REPORTED].isoformat(),
            reported_date=incident[INCIDENT_KEY_REPORTED_DATE],
            occurred=incident["Occurred"],
            comments=incident[INCIDENT_KEY_COMMENTS],
            disposition=incident["Disposition"],
            location=incident[INCIDENT_KEY_LOCATION],
            validated_address=incident[INCIDENT_KEY_ADDRESS],
            validated_location=GeoPt(
                incident[INCIDENT_KEY_LONGITUDE],
                incident[INCIDENT_KEY_LATITUDE],
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

    def download_all(self):
        """Download all incidents from datastore."""
        with self.client.context():
            query = Incident.query().order(-Incident.reported_date).fetch()

        json_incidents = []
        logging.info(f"Downloaded {len(query)} incident records.")
        for i in query:
            record = {}
            for key, value in i.to_dict().items():
                if isinstance(value, GeoPoint):
                    record[key] = (
                        str(value.latitude) + "," + str(value.longitude)
                    )
                    continue
                record[key] = value
            json_incidents.append(record)

        with open("incident_dump.csv", FILE_OPEN_MODE_WRITE) as csv_file:
            csv_writer = csv.DictWriter(
                csv_file,
                fieldnames=json_incidents[0].keys(),
                delimiter=",",
                quoting=csv.QUOTE_MINIMAL,
            )
            csv_writer.writeheader()
            csv_writer.writerows(json_incidents)
        logging.info(f"Saved {len(json_incidents)} incident records to a CSV.")
