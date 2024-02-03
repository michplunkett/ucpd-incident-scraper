import logging
from time import sleep
from typing import Optional

import requests
from censusgeocode import CensusGeocode
from googlemaps import Client

from incident_scraper.utils.constants import (
    ENV_GOOGLE_MAPS_KEY,
    INCIDENT_KEY_ADDRESS,
    INCIDENT_KEY_LATITUDE,
    INCIDENT_KEY_LONGITUDE,
    LOCATION_CHICAGO,
    LOCATION_HYDE_PARK,
    LOCATION_ILLINOIS,
    LOCATION_US,
)


class Geocoder:
    """
    A class that houses code for both the Census and Google Maps geocoders.
    """

    NUM_RETRIES = 10
    TIMEOUT = 5

    def __init__(self):
        self.address_cache = {}
        self.census_client = CensusGeocode()
        self.google_client = Client(ENV_GOOGLE_MAPS_KEY)

    def get_address_information(self, address: str, i_dict: dict) -> bool:
        if address in self.address_cache:
            self._get_address_from_cache(i_dict, self.address_cache[address])

        if (
            INCIDENT_KEY_ADDRESS not in i_dict
            and "between" not in address
            and " and " not in address
            and " to " not in address
        ):
            self._get_address_from_cache(
                i_dict, self._get_address_from_census(address)
            )

        if INCIDENT_KEY_ADDRESS not in i_dict:
            self._get_address_from_cache(
                i_dict, self._get_address_from_google(address)
            )

        # Return if an address was found.
        return INCIDENT_KEY_ADDRESS in i_dict

    def _get_address_from_census(self, address: str) -> dict:
        """Get address from Census geocoder.

        For more information on the Census Geocode API, visit this link:
        https://github.com/fitnr/censusgeocode#census-geocode
        """
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
            logging.debug(f"Using the Census geocoder for: {address}")
            coordinates = response[0]["coordinates"]
            self.address_cache[address] = {
                INCIDENT_KEY_ADDRESS: response[0]["matchedAddress"],
                INCIDENT_KEY_LATITUDE: coordinates["y"],
                INCIDENT_KEY_LONGITUDE: coordinates["x"],
            }
        else:
            self.address_cache[address] = None

        return self.address_cache[address]

    def _get_address_from_google(self, address: str) -> dict:
        """Get address from Google Maps geocoder.

        For more information on the Google Maps API, visit this link:
        https://github.com/googlemaps/google-maps-services-python#usage
        """
        resp = self.google_client.addressvalidation(
            [address],
            # Enable Coding Accuracy Support System
            enableUspsCass=True,
            locality=LOCATION_HYDE_PARK,
            regionCode=LOCATION_US,
        )

        result = resp["result"]
        if result:
            logging.debug(f"Using the Google Maps geocoder for: {address}")
            self.address_cache[address] = {
                INCIDENT_KEY_ADDRESS: result["address"][
                    "formattedAddress"
                ].replace(", USA", ""),
                INCIDENT_KEY_LATITUDE: result["geocode"]["location"][
                    "latitude"
                ],
                INCIDENT_KEY_LONGITUDE: result["geocode"]["location"][
                    "longitude"
                ],
            }
        else:
            self.address_cache[address] = None

        return self.address_cache[address]

    @staticmethod
    def _get_address_from_cache(i_dict: dict, result: Optional[dict]):
        if i_dict and result:
            i_dict[INCIDENT_KEY_ADDRESS] = result[INCIDENT_KEY_ADDRESS]
            i_dict[INCIDENT_KEY_LATITUDE] = result[INCIDENT_KEY_LATITUDE]
            i_dict[INCIDENT_KEY_LONGITUDE] = result[INCIDENT_KEY_LONGITUDE]
