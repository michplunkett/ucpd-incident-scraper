"""Initialize and set the logging defaults."""

import json
import logging
import sys

from google.cloud.logging_v2.handlers import StructuredLogHandler
from google.oauth2 import service_account

from incident_scraper.utils.constants import (
    ENV_GCP_CREDENTIALS,
    FILE_TYPE_JSON,
)


def init_logger():
    """Set logger defaults."""
    if not ENV_GCP_CREDENTIALS.endswith(FILE_TYPE_JSON):
        # Only need credentials if running outside a GCP environment
        service_account.Credentials.from_service_account_info(
            json.loads(ENV_GCP_CREDENTIALS)
        )

    logger = logging.getLogger("ucpd-incident-scraper")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = StructuredLogHandler(stream=sys.stdout)
        logger.addHandler(handler)
        logger.propagate = False

    return logger
