"""Contains the headers class."""
import json
import os
import random


class Headers:
    """Class that contains all headers in external header file."""

    def __init__(self):
        self.list_of_headers = []
        self._load_headers_file()

    def _load_headers_file(self):
        """Load the list of headers."""
        path = (
            os.getcwd().replace("\\", "/")
            + "/incident_scraper/data/http_headers.json"
        )
        print(path)
        with open(path, "r") as json_file:
            self.list_of_headers = json.load(json_file)

    def get_random_header(self):
        """Use random number generator to get random header from list."""
        return self.list_of_headers[
            random.randint(0, len(self.list_of_headers))
        ]
