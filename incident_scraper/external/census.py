"""Contains code relating to the Census Geocode API."""
import logging
from time import sleep

import requests
from censusgeocode import CensusGeocode

from incident_scraper.utils.constants import LOCATION_CHICAGO, LOCATION_ILLINOIS


class CensusClient:
    """Create the Census API client and use it to validate addresses."""

    NUM_RETRIES = 10
    TIMEOUT = 5

    def __init__(self):
        self.client = CensusGeocode()
        self.address_cache = {}

    def validate_address(self, address: str):
        """Validate address parameter and return Census result.

        For more information on the Census Geocode API, visit this link:
        https://github.com/fitnr/censusgeocode#census-geocode
        """
        if address in self.address_cache:
            return self.address_cache[address]

        response = None
        for _ in range(self.NUM_RETRIES):
            try:
                response = self.client.address(
                    street=address,
                    city=LOCATION_CHICAGO,
                    state=LOCATION_ILLINOIS,
                    returntype="locations",
                    timeout=self.TIMEOUT,
                )
                if response:
                    break
            except requests.exceptions.RequestException:
                logging.info(
                    f"Pausing {self.TIMEOUT}s between Census Geocode requests."
                )
                sleep(self.TIMEOUT)
                pass

        if response:
            coordinates = response[0]["coordinates"]
            self.address_cache[address] = (
                response[0]["matchedAddress"],
                coordinates["x"],
                coordinates["y"],
            )
        else:
            self.address_cache[address] = None

        return self.address_cache[address]
