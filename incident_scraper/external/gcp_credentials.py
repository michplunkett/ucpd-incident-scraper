"""Credential loading shared by the GCP clients."""

import json

from google.oauth2 import service_account

from incident_scraper.utils.constants import (
    ENV_GCP_CREDENTIALS,
    FILE_TYPE_JSON,
)


def get_gcp_credentials() -> service_account.Credentials | None:
    """
    Get service account credentials, or None to use the default ones.

    GOOGLE_APPLICATION_CREDENTIALS holds either a path to a JSON key file (which
    the GCP clients find on their own) or the key's contents.
    """
    if ENV_GCP_CREDENTIALS.endswith(FILE_TYPE_JSON):
        return None

    return service_account.Credentials.from_service_account_info(
        json.loads(ENV_GCP_CREDENTIALS)
    )
