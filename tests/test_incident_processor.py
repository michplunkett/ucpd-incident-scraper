"""Test the processing of scraped incidents before they are saved."""

import logging
from datetime import datetime

import pytest

from incident_scraper.services.incident_processor import IncidentProcessor
from incident_scraper.utils.constants import (
    INCIDENT_KEY_ADDRESS,
    INCIDENT_KEY_COMMENTS,
    INCIDENT_KEY_ID,
    INCIDENT_KEY_LATITUDE,
    INCIDENT_KEY_LOCATION,
    INCIDENT_KEY_LONGITUDE,
    INCIDENT_KEY_REPORTED,
    INCIDENT_KEY_REPORTED_DATE,
    INCIDENT_KEY_SEASON,
    INCIDENT_KEY_TYPE,
    INCIDENT_PREDICTED_TYPE,
    TIMEZONE_CHICAGO,
)

# Marks a field of the raw incident that a test wants removed.
DROP = object()

VALID_LATITUDE = 41.79
VALID_LONGITUDE = -87.6
VALID_COORDINATES = (VALID_LATITUDE, VALID_LONGITUDE)


class FakeDatastore:
    def __init__(self):
        self.saved_batches = []

    def add_incidents(self, incidents):
        self.saved_batches.append(list(incidents))

    @property
    def saved(self):
        return [i for batch in self.saved_batches for i in batch]


class FakeAddressParser:
    @staticmethod
    def process(address):
        return address


class FakeGeocoder:
    """Gives every address the same coordinates, or finds none if unset."""

    def __init__(self, coordinates=None):
        self._coordinates = coordinates

    def get_address_information(self, address, incident):
        if self._coordinates is None:
            return False

        latitude, longitude = self._coordinates
        incident[INCIDENT_KEY_ADDRESS] = address
        incident[INCIDENT_KEY_LATITUDE] = latitude
        incident[INCIDENT_KEY_LONGITUDE] = longitude
        return True


class FakeClassifier:
    def __init__(self, prediction=None):
        self._prediction = prediction
        self.comments_seen = []

    def get_predicted_incident_type(self, comment):
        self.comments_seen.append(comment)
        return self._prediction


def make_raw_incident(**overrides):
    incident = {
        INCIDENT_KEY_TYPE: "Theft",
        INCIDENT_KEY_LOCATION: "Ellis Ave (Reynolds Club)",
        INCIDENT_KEY_REPORTED: "1/5/24 3:45PM",
        "Occurred": "1/5/24 3:00 PM",
        INCIDENT_KEY_COMMENTS: "  Stolen   bike\nfrom rack ",
        "Disposition": "Open",
    }
    incident.update(overrides)
    return {k: v for k, v in incident.items() if v is not DROP}


@pytest.fixture
def datastore():
    return FakeDatastore()


@pytest.fixture
def make_processor(datastore):
    def _make_processor(coordinates=VALID_COORDINATES, prediction=None):
        classifier = FakeClassifier(prediction)
        processor = IncidentProcessor(
            nbd_client=datastore,
            addr_parser=FakeAddressParser(),
            geocoder=FakeGeocoder(coordinates),
            classifier=classifier,
            lemmatize=str.strip,
        )
        return processor, classifier

    return _make_processor


@pytest.mark.parametrize(
    ("overrides", "coordinates", "expect_saved"),
    [
        ({}, VALID_COORDINATES, True),
        ({"Extra": "field"}, VALID_COORDINATES, False),
        ({"Occurred": DROP}, VALID_COORDINATES, False),
        ({INCIDENT_KEY_REPORTED: "not a date"}, VALID_COORDINATES, False),
        ({}, None, False),
        ({}, (91.0, VALID_LONGITUDE), False),
        ({}, (VALID_LATITUDE, -90.5), False),
    ],
    ids=[
        "valid",
        "too-many-fields",
        "too-few-fields",
        "unparseable-date",
        "geocoder-finds-nothing",
        "latitude-out-of-range",
        "longitude-out-of-range",
    ],
)
def test_only_valid_incidents_are_saved(
    make_processor, datastore, overrides, coordinates, expect_saved
):
    processor, _ = make_processor(coordinates)

    processor.process_and_save({"UC1": make_raw_incident(**overrides)})

    assert len(datastore.saved) == int(expect_saved)


def test_saved_incident_is_cleaned_and_enriched(make_processor, datastore):
    processor, _ = make_processor()

    processor.process_and_save({"UC1": make_raw_incident()})

    (saved,) = datastore.saved
    assert saved[INCIDENT_KEY_ID] == "UC1"
    assert saved[INCIDENT_KEY_COMMENTS] == "Stolen bike from rack"
    assert saved[INCIDENT_KEY_ADDRESS] == "Ellis Ave"
    assert saved[INCIDENT_KEY_REPORTED_DATE] == "2024-01-05"
    assert saved[INCIDENT_KEY_SEASON] == "Winter"
    assert saved[INCIDENT_PREDICTED_TYPE] == ""
    assert saved[INCIDENT_KEY_REPORTED] == TIMEZONE_CHICAGO.localize(
        datetime(2024, 1, 5, 15, 45)
    )


@pytest.mark.parametrize(
    ("incident_type", "prediction", "expected_prediction", "expected_calls"),
    [
        ("Information", "Theft", "Theft", 1),
        ("Information", None, "", 1),
        ("Theft", "Battery", "", 0),
    ],
    ids=["predicted", "no-prediction", "not-information"],
)
def test_only_information_incidents_are_predicted(
    make_processor,
    datastore,
    incident_type,
    prediction,
    expected_prediction,
    expected_calls,
):
    processor, classifier = make_processor(prediction=prediction)

    processor.process_and_save(
        {"UC1": make_raw_incident(**{INCIDENT_KEY_TYPE: incident_type})}
    )

    (saved,) = datastore.saved
    assert saved[INCIDENT_PREDICTED_TYPE] == expected_prediction
    assert classifier.comments_seen == (
        ["Stolen bike from rack"] * expected_calls
    )


@pytest.mark.parametrize(
    ("incident_count", "expected_batch_sizes"),
    [
        (0, []),
        (1, [1]),
        (100, [100]),
        (101, [100, 1]),
        (250, [100, 100, 50]),
    ],
)
def test_incidents_are_saved_in_batches(
    make_processor, datastore, incident_count, expected_batch_sizes
):
    processor, _ = make_processor()
    incidents = {f"UC{n}": make_raw_incident() for n in range(incident_count)}

    processor.process_and_save(incidents)

    assert [len(b) for b in datastore.saved_batches] == expected_batch_sizes


@pytest.mark.parametrize(
    ("overrides", "coordinates", "expected_log"),
    [
        ({"Extra": "field"}, VALID_COORDINATES, "1 of 1 contained malformed"),
        ({}, None, "1 of 1 could not be processed by the Geocoder."),
        ({}, VALID_COORDINATES, "1 of 1 incidents were successfully"),
    ],
    ids=["malformed", "geocoder-failure", "success"],
)
def test_each_incident_is_counted_once_in_the_summary(
    make_processor, caplog, overrides, coordinates, expected_log
):
    caplog.set_level(logging.INFO)
    processor, _ = make_processor(coordinates)

    processor.process_and_save({"UC1": make_raw_incident(**overrides)})

    assert expected_log in caplog.text
