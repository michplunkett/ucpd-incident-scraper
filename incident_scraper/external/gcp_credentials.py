"""Contains the credential loading that is shared by the GCP clients."""

import json

from google.oauth2 import service_account

from incident_scraper.utils.constants import (
    ENV_GCP_CREDENTIALS,
    FILE_TYPE_JSON,
)


def get_gcp_credentials() -> service_account.Credentials | None:
    """
    Get the service account credentials for the GCP clients.

    GOOGLE_APPLICATION_CREDENTIALS is either the path to a JSON key file, which
    the GCP clients find on their own (None is returned), or the contents of
    the key itself.
    """
    if ENV_GCP_CREDENTIALS.endswith(FILE_TYPE_JSON):
        return None

    return service_account.Credentials.from_service_account_info(
        json.loads(ENV_GCP_CREDENTIALS)
    )
