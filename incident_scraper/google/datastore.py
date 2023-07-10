"""Contains code relating to the Google Cloud Platform Datastore service."""
from google.cloud.datastore import Client


def get_client():
    """Get GCP client.

    Returns
    -------
    datastore.Client
        A GCP client that allows you to easily interact with the GCP Datastore.
    """
    return Client()
