"""Contains the GoogleMaps API functions."""
from googlemaps import Client

from incident_scraper.utils.constants import (
    ENV_GOOGLE_MAPS_KEY,
    LOCATION_CHICAGO,
    LOCATION_US,
)


class GoogleMaps:
    """Create the client and access Google Maps functionality."""

    def __init__(self):
        self.client = Client(ENV_GOOGLE_MAPS_KEY)

    def get_address(self, address: str):
        """Get valid address from Google Maps."""
        resp = self.client.addressvalidation(
            [address],
            # Enable Coding Accuracy Support System
            enableUspsCass=True,
            locality=LOCATION_CHICAGO,
            regionCode=LOCATION_US,
        )

        result = resp["result"]
        if result:
            return result
        else:
            return None
