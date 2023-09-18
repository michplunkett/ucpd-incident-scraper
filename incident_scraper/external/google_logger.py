"""Initialize and set the logging defaults."""
import json
import logging
import sys

import google.cloud.logging as gcp_logging
from google.oauth2 import service_account

from incident_scraper.utils.constants import (
    ENV_GCP_CREDENTIALS,
    ENV_GCP_PROJECT_ID,
)


def init_logger():
    """Set logger defaults."""
    if ENV_GCP_CREDENTIALS.endswith(".json"):
        logging_client = gcp_logging.Client(project=ENV_GCP_PROJECT_ID)
    else:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(ENV_GCP_CREDENTIALS)
        )
        logging_client = gcp_logging.Client(
            credentials=credentials, project=ENV_GCP_PROJECT_ID
        )

    logging_client.setup_logging(log_level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
