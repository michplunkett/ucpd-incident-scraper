"""Contains the Incident model and all of its associated information."""

from google.cloud.ndb import GeoPtProperty, Model, StringProperty

from incident_scraper.utils.constants import (
    INCIDENT_KEY_ADDRESS,
    INCIDENT_KEY_LATITUDE,
    INCIDENT_KEY_LONGITUDE,
)


class Incident(Model):
    """Standard data structure for recovered UCPD incidents."""

    ucpd_id = StringProperty(indexed=True)
    incident = StringProperty(indexed=True)
    predicted_incident = StringProperty()
    reported = StringProperty()
    reported_date = StringProperty(indexed=True)
    occurred = StringProperty()
    comments = StringProperty()
    disposition = StringProperty()
    location = StringProperty()
    validated_address = StringProperty()
    validated_location = GeoPtProperty()


def set_census_validated_location(scrape: dict, resp: list):
    """Set the validated location properties from the Census response."""
    if not resp:
        return False

    scrape[INCIDENT_KEY_ADDRESS] = resp[0]
    scrape[INCIDENT_KEY_LATITUDE] = resp[1]
    scrape[INCIDENT_KEY_LONGITUDE] = resp[2]

    return True


KEY_ADDRESS = "address"
KEY_GEOCODE = "geocode"


def set_google_maps_validated_location(scrape: dict, resp: list):
    """Set the validated location properties from the Census response."""
    if not resp:
        return False

    if resp[KEY_GEOCODE]:
        location = resp[KEY_GEOCODE]["location"]
        scrape[INCIDENT_KEY_LATITUDE] = location["latitude"]
        scrape[INCIDENT_KEY_LONGITUDE] = location["longitude"]

    if resp[KEY_ADDRESS]:
        scrape[INCIDENT_KEY_ADDRESS] = resp[KEY_ADDRESS]["formattedAddress"]
    else:
        return False

    return True
