"""Initialize and set the logging defaults."""

import logging
import sys

import google.cloud.logging as gcp_logging

from incident_scraper.external.gcp_credentials import get_gcp_credentials
from incident_scraper.utils.constants import ENV_GCP_PROJECT_ID


def init_logger():
    """Set logger defaults."""
    logging_client = gcp_logging.Client(
        project=ENV_GCP_PROJECT_ID, credentials=get_gcp_credentials()
    )

    logging_client.setup_logging(log_level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
