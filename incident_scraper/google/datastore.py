"""Contains code relating to the Google Cloud Platform Datastore service."""
import os

from google.cloud.datastore import Client

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")


class Datastore:
    """Create the client and access GCP datastore functionality."""

    def __init__(self):
        self.client = Client(project_id)

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
