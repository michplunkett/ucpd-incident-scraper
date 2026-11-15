"""Initialize and set the logging defaults."""

import logging
import sys

import google.cloud.logging as gcp_logging

from incident_scraper.external.gcp_credentials import get_gcp_credentials
from incident_scraper.utils.constants import ENV_GCP_PROJECT_ID


def init_logger() -> gcp_logging.Client:
    """Set logger defaults and return the logging client."""
    logging_client = gcp_logging.Client(
        project=ENV_GCP_PROJECT_ID, credentials=get_gcp_credentials()
    )

    logging_client.setup_logging(log_level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    return logging_client


def shutdown_logger(logging_client: gcp_logging.Client) -> None:
    """
    Flush pending logs and close the client before the interpreter shuts down.

    Since Python 3.12, the handler's thread can't send its queue at shutdown,
    so those logs are dropped. Flush first: close() ends the connection before
    it closes the handlers.
    """
    logging_client.flush_handlers()
    logging_client.close()
