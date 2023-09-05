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


def set_validated_location(scrape_response: dict, census_response: str):
    """Set the validated locations properties."""
    if not census_response:
        return False

    scrape_response["ValidatedAddress"] = census_response[0]
    scrape_response["ValidatedLatitude"] = census_response[1]
    scrape_response["ValidatedLongitude"] = census_response[2]

    return True
