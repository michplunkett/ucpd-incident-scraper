"""Initialize and set the logging defaults."""
import json
import logging
import sys

import google.cloud.logging as gcp_logging

from incident_scraper.utils.constants import ENV_CREDENTIALS, ENV_PROJECT_ID


def init_logger():
    """Set logger defaults."""
    if ENV_CREDENTIALS.endswith(".json"):
        logging_client = gcp_logging.Client(project=ENV_PROJECT_ID)
    else:
        logging_client = gcp_logging.Client(
            credentials=json.loads(ENV_CREDENTIALS), project=ENV_PROJECT_ID
        )

    logging_client.setup_logging(log_level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
