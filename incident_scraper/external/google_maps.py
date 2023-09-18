"""Contains the GoogleMaps API functions."""
from googlemaps import Client

from incident_scraper.utils.constants import ENV_GOOGLE_MAPS_KEY


class GoogleMaps:
    """Create the client and access Google Maps functionality."""

    def __init__(self):
        self.client = Client(ENV_GOOGLE_MAPS_KEY)

    def get_address(self, address: str):
        """Get valid address from Google Maps."""
        result = self.client.addressvalidation(
            [address],
            # Enable Coding Accuracy Support System
            enableUspsCass=True,
            locality="Chicago",
            regionCode="US",
        )

        if result["result"] and result["result"]["verdict"]["addressComplete"]:
            return result["result"]
        else:
            return None
