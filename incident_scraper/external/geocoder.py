import logging
from time import sleep

import requests
from censusgeocode import CensusGeocode
from googlemaps import Client

from incident_scraper.utils.constants import ENV_GOOGLE_MAPS_KEY, \
    LOCATION_CHICAGO, LOCATION_US, LOCATION_ILLINOIS, INCIDENT_KEY_ADDRESS, \
    INCIDENT_KEY_LATITUDE, INCIDENT_KEY_LONGITUDE


class Geocoder:
    """A class that houses code for both the Census and Google Maps geocoders."""
    KEY_ADDRESS = "address"
    KEY_GEOCODE = "geocode"
    NUM_RETRIES = 10
    TIMEOUT = 5


    def __init__(self):
        self.address_cache = {}
        self.census_client = CensusGeocode()
        self.google_client = Client(ENV_GOOGLE_MAPS_KEY)


    def get_address_information(self, address: str, i_dict: dict) -> bool:
        if "between" not in address and " and " not in address:
            self._get_address_from_census(address)

        if INCIDENT_KEY_ADDRESS not in i_dict:
            self._get_address_from_google(address)

        # Return if an address was found.
        return INCIDENT_KEY_ADDRESS in i_dict

    def _get_address_from_census(self, address: str) -> dict:
        """Get address from Census geocoder.

        For more information on the Census Geocode API, visit this link:
        https://github.com/fitnr/censusgeocode#census-geocode
        """
        if address in self.address_cache:
            return self.address_cache[address]

        response = None
        for _ in range(self.NUM_RETRIES):
            try:
                response = self.census_client.address(
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

    def _get_address_from_google(self, address: str) -> dict:
        """Get address from Google Maps geocoder.

        For more information on the Google Maps API, visit this link:
        https://github.com/googlemaps/google-maps-services-python?tab=readme-ov-file#usage
        """
        if address in self.address_cache:
            return self.address_cache[address]

        resp = self.google_client.addressvalidation(
            [address],
            # Enable Coding Accuracy Support System
            enableUspsCass=True,
            locality=LOCATION_CHICAGO,
            regionCode=LOCATION_US,
        )

        result = resp["result"]
        if result:
            self.address_cache[address] = result
        else:
            self.address_cache[address] = None

        return self.address_cache[address]

    @staticmethod
    def set_census_validated_location(scrape: dict, resp: list) -> None:
        """Set the validated location properties from the Census response."""
        scrape[INCIDENT_KEY_ADDRESS] = resp[0]
        scrape[INCIDENT_KEY_LATITUDE] = resp[1]
        scrape[INCIDENT_KEY_LONGITUDE] = resp[2]

    @staticmethod
    def set_google_maps_validated_location(scrape: dict, resp: list) -> None:
        """Set the validated location properties from the Census response."""
        if "geocode" in resp and "address" in resp:
            location = resp["geocode"]["location"]
            scrape[INCIDENT_KEY_LATITUDE] = location["latitude"]
            scrape[INCIDENT_KEY_LONGITUDE] = location["longitude"]
            scrape[INCIDENT_KEY_ADDRESS] = resp["address"]["formattedAddress"]

