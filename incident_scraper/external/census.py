"""Contains code relating to the Census Geocode API."""
from time import sleep

import requests
from censusgeocode import CensusGeocode


class CensusClient:
    """Create the Census API client and use it to validate addresses."""

    NUM_RETRIES = 10
    TIMEOUT = 5

    def __init__(self):
        self.client = CensusGeocode()

    def validate_address(self, address: str):
        """Validate address parameter and return Census result.

        For more information on the Census Geocode API, visit this link:
        https://github.com/fitnr/censusgeocode#census-geocode
        """
        response = None
        for _ in range(self.NUM_RETRIES):
            try:
                response = self.client.address(
                    street=address,
                    city="Chicago",
                    state="IL",
                    returntype="locations",
                    timeout=self.TIMEOUT,
                )
                if response:
                    break
            except requests.exceptions.RequestException:
                print(
                    f"Pausing {self.TIMEOUT}s between Census Geocode requests."
                )
                sleep(self.TIMEOUT)
                pass

        if response:
            coordinates = response[0]["coordinates"]
            return (
                response[0]["matchedAddress"],
                coordinates["x"],
                coordinates["y"],
            )
        else:
            return None
