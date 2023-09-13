"""Initialize and set the logging defaults."""
import logging
import sys

import google.cloud.logging as gcp_logging


def init_logger():
    logging_client = gcp_logging.Client()
    logging_client.setup_logging(log_level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
