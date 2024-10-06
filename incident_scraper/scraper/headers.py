"""Contains the headers class."""

import gzip
import json
import os
import random

from incident_scraper.utils.constants import FILE_ENCODING_UTF_8, FILE_OPEN_READ


class Headers:
    """Class that contains all headers in external header file."""

    def __init__(self, seed=None):
        random.seed(seed)
        self._list_of_headers = []
        self._load_headers_file()

    def _load_headers_file(self):
        """Load the list of headers."""
        file_path = (
            os.getcwd().replace("\\", "/")
            + "/incident_scraper/data/http_headers.json.gz"
        )

        with gzip.open(file_path, FILE_OPEN_READ) as f:
            self._list_of_headers = json.loads(
                f.read().decode(FILE_ENCODING_UTF_8)
            )

    def get_random_header(self):
        """Use random number generator to get random header from list."""
        return self._list_of_headers[
            random.randint(0, len(self._list_of_headers) - 1)
        ]
