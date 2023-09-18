"""Contains the Incident model and all of its associated information."""

from google.cloud.ndb import GeoPtProperty, Model, StringProperty


class Incident(Model):
    """Standard data structure for recovered UCPD incidents."""

    ucpd_id = StringProperty(indexed=True)
    incident = StringProperty(indexed=True)
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

    scrape["ValidatedAddress"] = resp[0]
    scrape["ValidatedLatitude"] = resp[1]
    scrape["ValidatedLongitude"] = resp[2]

    return True


def set_google_maps_validated_location(scrape: dict, resp: list):
    """Set the validated location properties from the Census response."""
    if not resp:
        return False

    if resp["geocode"]:
        location = resp["geocode"]["location"]
        scrape["ValidatedLatitude"] = location["latitude"]
        scrape["ValidatedLongitude"] = location["longitude"]

    if resp["address"]:
        scrape["ValidatedAddress"] = resp["address"]["formattedAddress"]
    else:
        return False

    return True
