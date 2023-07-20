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
        """Add Incident to datastore."""
        gcp_incident = Entity(
            key=self.client.key(self.ENTITY_TYPE, incident.ucpd_id)
        )
        gcp_incident.update(serialize(incident))
        self.client.put(gcp_incident)

    def add_incidents(self, incidents: [Incident]):
        """Add Incidents to datastore in bulk."""
        json_incidents = []
        for i in incidents:
            gcp_incident = Entity(
                key=self.client.key(self.ENTITY_TYPE, i.ucpd_id)
            )
            gcp_incident.update(serialize(i))
            json_incidents.append(gcp_incident)
        self.client.put_multi(json_incidents)

    def get_incident(self, ucpd_id: str):
        """Get Incident from datastore."""
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
