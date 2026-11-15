"""Contains the headers class."""

import gzip
import json
import random
from importlib.resources import files

_HEADERS_FILE = files("incident_scraper") / "data" / "http_headers.json.gz"


class Headers:
    """Class that contains all headers in external header file."""

    def __init__(self, seed=None):
        random.seed(seed)
        self._list_of_headers = []
        self._load_headers_file()

    def _load_headers_file(self):
        """Load the list of headers."""
        with _HEADERS_FILE.open("rb") as raw_file, gzip.open(raw_file) as f:
            self._list_of_headers = json.load(f)

    def get_random_header(self):
        """Use random number generator to get random header from list."""
        return self._list_of_headers[
            random.randint(0, len(self._list_of_headers) - 1)
        ]
