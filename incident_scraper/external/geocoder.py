import re
from time import sleep
from typing import Optional

import requests
from censusgeocode import CensusGeocode
from googlemaps import Client

from incident_scraper.external.google_logger import init_logger
from incident_scraper.models.address_parser import AddressParser
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


logger = init_logger()


class Geocoder:
    """
    A class that houses code for both the Census and Google Maps geocoders.
    """

    NON_FINDABLE_ADDRESS_DICT = {
        INCIDENT_KEY_ADDRESS: "",
        INCIDENT_KEY_LATITUDE: 0.0,
        INCIDENT_KEY_LONGITUDE: 0.0,
    }
    NUM_RETRIES = 10
    TIMEOUT = 5

    def __init__(self):
        self._address_cache = {}
        self._address_parser = AddressParser()
        self._census_client = CensusGeocode()
        self._google_client = Client(ENV_GOOGLE_MAPS_KEY)

    def get_address_information(self, address: str, i_dict: dict) -> bool:
        if address in self._address_cache:
            self._get_address_from_cache(i_dict, self._address_cache[address])

        if (
            INCIDENT_KEY_ADDRESS not in i_dict
            and "between" not in address.lower()
            and " and " not in address
            and " to " not in address
            and " at " not in address
        ):
            self._get_address_from_cache(
                i_dict, self._census_validate_address(address)
            )

        if INCIDENT_KEY_ADDRESS not in i_dict:
            self._get_address_from_cache(
                i_dict, self._parse_and_process_address(address)
            )

        # Return if an address was found.
        return INCIDENT_KEY_ADDRESS in i_dict

    @staticmethod
    def _cannot_geocode(address: str, and_cnt: [str]) -> bool:
        return (
            " to " in address
            or " or " in address
            or "Out of Area" in address
            or and_cnt > 1
        )

    def _parse_and_process_address(self, address: str) -> dict:
        address_lower = address.lower()
        and_cnt = len([s for s in address_lower.split() if s == "and"])

        if self._cannot_geocode(address, and_cnt):
            logger.error(f"Unable to process and geocode address: {address}")
            self._address_cache[address] = self.NON_FINDABLE_ADDRESS_DICT
        elif " between " in address_lower:
            self._parse_between_addresses(address)
        elif and_cnt == 1 or " at " in address_lower:
            self._process_at_and_addresses(address)
        elif re.match(r"^\d+ [ES]{1}\. ", address):
            self._google_validate_address(address)
        else:
            logger.error(f"Unable to process and geocode address: {address}")
            self._address_cache[address] = self.NON_FINDABLE_ADDRESS_DICT

        return self._address_cache[address]

    def _parse_between_addresses(self, address: str) -> dict:
        processed_addresses = self._address_parser.process_between_streets(
            address
        )

        if len(processed_addresses) == 2:
            addr_one = self._google_validate_address(processed_addresses[0])
            addr_two = self._google_validate_address(processed_addresses[1])
            avg_longitude: float = (
                addr_one[INCIDENT_KEY_LONGITUDE]
                + addr_two[INCIDENT_KEY_LONGITUDE]
            ) / 2.0
            self._google_validate_coordinates(
                address, avg_longitude, addr_one[INCIDENT_KEY_LATITUDE]
            )
        elif len(processed_addresses) == 1:
            self._address_cache[address] = self._google_validate_address(
                processed_addresses[0]
            )
        else:
            self._address_cache[address] = self.NON_FINDABLE_ADDRESS_DICT

        return self._address_cache[address]

    def _process_at_and_addresses(self, address: str) -> dict:
        processed_address = self._address_parser.process_at_and_streets(address)

        self._address_cache[address] = self._google_validate_address(
            processed_address
        )

        return self._address_cache[address]

    def _census_validate_address(self, address: str) -> dict:
        """Get address from Census geocoder.

        For more information on the Census Geocode API, visit this link:
        https://github.com/fitnr/censusgeocode#census-geocode
        """
        response = None
        for _ in range(self.NUM_RETRIES):
            try:
                response = self._census_client.address(
                    street=address,
                    city=LOCATION_CHICAGO,
                    state=LOCATION_ILLINOIS,
                    returntype="locations",
                    timeout=self.TIMEOUT,
                )
                if response:
                    break
            except requests.exceptions.RequestException:
                logger.info(
                    f"Pausing {self.TIMEOUT}s between Census Geocode requests."
                )
                sleep(self.TIMEOUT)
                pass

        if response:
            logger.debug(f"Using the Census geocoder for: {address}")
            coordinates = response[0]["coordinates"]
            self._address_cache[address] = {
                INCIDENT_KEY_ADDRESS: response[0]["matchedAddress"],
                INCIDENT_KEY_LATITUDE: coordinates["y"],
                INCIDENT_KEY_LONGITUDE: coordinates["x"],
            }
        else:
            logger.debug(
                f"Unable to get result from the Census geocoder for: {address}"
            )
            self._address_cache[address] = None

        return self._address_cache[address]

    def _google_validate_coordinates(
        self, original_addr: str, longitude: float, latitude: float
    ) -> dict:
        logger.debug(
            "Using the Google Maps reverse geocoder for: "
            f"{latitude}, {longitude}"
        )
        resp = self._google_client.reverse_geocode((latitude, longitude))

        if resp:
            self._address_cache[original_addr] = {
                INCIDENT_KEY_ADDRESS: resp[0]["formatted_address"].replace(
                    ", USA", ""
                ),
                INCIDENT_KEY_LATITUDE: resp[0]["geometry"]["location"]["lat"],
                INCIDENT_KEY_LONGITUDE: resp[0]["geometry"]["location"]["lng"],
            }
        else:
            logger.debug(
                "Unable to get result from the Google Maps reverse geocoder "
                f"for: {latitude}, {longitude}"
            )
            self._address_cache[original_addr] = None

        return self._address_cache[original_addr]

    def _google_validate_address(self, address: str) -> dict:
        """Get address from Google Maps geocoder.

        For more information on the Google Maps API, visit this link:
        https://github.com/googlemaps/google-maps-services-python#usage
        """
        resp = self._google_client.addressvalidation(
            [address],
            # Enable Coding Accuracy Support System
            enableUspsCass=True,
            locality=LOCATION_HYDE_PARK,
            regionCode=LOCATION_US,
        )

        result = resp["result"]
        if result:
            logger.debug(f"Using the Google Maps geocoder for: {address}")
            self._address_cache[address] = {
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
            logger.debug(
                "Unable to get result from the Google Maps geocoder "
                f"for: {address}"
            )
            self._address_cache[address] = None

        return self._address_cache[address]

    @staticmethod
    def _get_address_from_cache(i_dict: dict, result: Optional[dict]):
        if i_dict and result:
            i_dict[INCIDENT_KEY_ADDRESS] = result[INCIDENT_KEY_ADDRESS]
            i_dict[INCIDENT_KEY_LATITUDE] = result[INCIDENT_KEY_LATITUDE]
            i_dict[INCIDENT_KEY_LONGITUDE] = result[INCIDENT_KEY_LONGITUDE]
