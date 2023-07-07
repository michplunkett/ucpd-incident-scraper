"""Contains code to create and get the Google Cloud Platform client."""
from google.cloud.datastore import Client


def get_gcp_data_store_client():
    """Get GCP client.

    Returns
    -------
    datastore.Client
        A GCP client that allows you to easily interact with the GCP Datastore.
    """
    return Client()
