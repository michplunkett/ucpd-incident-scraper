"""Contains code relating to the Google Cloud Platform Datastore service."""
import os

from google.cloud.datastore import Client, Entity
from jsonic import deserialize, serialize

from incident_scraper.models.incident import Incident


class GoogleDatastore:
    """Create the client and access GCP datastore functionality."""

    ENTITY_TYPE = "Incident"
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

    def __init__(self):
        self.client = Client(self.PROJECT_ID)

    def add_incident(self, incident: Incident):
        """Add incident to datastore."""
        complete_key = self.client.key(self.ENTITY_TYPE, incident.ucpd_id)

        gcp_incident = Entity(key=complete_key)
        gcp_incident.update(serialize(incident))
        self.client.put(gcp_incident)

    def get_incident(self, ucpd_id: str):
        """Get incident from datastore."""
        datastore_response = self.client.get(
            self.client.key(self.ENTITY_TYPE, ucpd_id)
        )
        if datastore_response:
            return Incident(gcp_response=deserialize(datastore_response))
        else:
            return None

    def remove_incident(self, ucpd_id: str):
        """Remove incident from datastore."""
        self.client.delete(self.client.key(self.ENTITY_TYPE, ucpd_id))
