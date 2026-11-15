"""Turns scraped UCPD incidents into records for the GCP Datastore."""

import logging
from collections.abc import Callable, Sequence
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

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
    INCIDENT_TYPE_INFO,
    TIMEZONE_CHICAGO,
    UCPD_MDY_KEY_DATE_FORMAT,
)
from incident_scraper.utils.functions import (
    chunked,
    clean_comments,
    determine_season,
    normalize_reported_timestamp,
    parse_reported_timestamp,
)

if TYPE_CHECKING:
    from incident_scraper.external.geocoder import Geocoder
    from incident_scraper.external.google_nbd import GoogleNBD
    from incident_scraper.models.address_parser import AddressParser
    from incident_scraper.models.classifier import Classifier

ScrapedIncident = dict[str, Any]


class Outcome(Enum):
    """The result of processing a scraped incident."""

    READY = auto()
    MALFORMED = auto()
    GEOCODE_FAILED = auto()


class IncidentProcessor:
    """Validate, enrich, and save scraped incidents in batches."""

    BATCH_SIZE = 100
    EXPECTED_FIELD_COUNT = 6

    def __init__(
        self,
        nbd_client: GoogleNBD,
        addr_parser: AddressParser,
        geocoder: Geocoder,
        classifier: Classifier,
        lemmatize: Callable[[str], str],
    ):
        self._nbd_client = nbd_client
        self._addr_parser = addr_parser
        self._geocoder = geocoder
        self._classifier = classifier
        self._lemmatize = lemmatize
        self._information_total = 0
        self._information_predicted = 0

    def process_and_save(self, incidents: dict[str, ScrapedIncident]) -> None:
        """Save the valid scraped incidents to the Datastore."""
        total_incidents = len(incidents)
        logging.info(
            f"{total_incidents} total incidents were scraped from the UCPD "
            "Incidents' site."
        )

        self._information_total = 0
        self._information_predicted = 0
        total_added = 0
        for batch in chunked(list(incidents.items()), self.BATCH_SIZE):
            total_added += self._process_batch(batch)

        logging.info(
            f"{self._information_predicted} of {self._information_total} "
            "'Information' incidents predicted into other categories."
        )
        logging.info(
            f"{total_incidents - total_added} of {total_incidents} "
            "incidents could NOT be added to the GCP Datastore."
        )

    def _process_batch(
        self, batch: Sequence[tuple[str, ScrapedIncident]]
    ) -> int:
        """Process a batch and return how many incidents were added."""
        incidents_by_outcome: dict[Outcome, list[ScrapedIncident]] = {
            outcome: [] for outcome in Outcome
        }
        for key, incident in batch:
            outcome = self._process_incident(key, incident)
            incidents_by_outcome[outcome].append(incident)

        ready = incidents_by_outcome[Outcome.READY]
        batch_size = len(batch)
        logging.info(
            f"{len(incidents_by_outcome[Outcome.MALFORMED])} of {batch_size} "
            "contained malformed or voided information."
        )
        logging.info(
            f"{len(incidents_by_outcome[Outcome.GEOCODE_FAILED])} of "
            f"{batch_size} could not be processed by the Geocoder."
        )
        logging.info(
            f"{len(ready)} of {batch_size} incidents were successfully "
            "processed."
        )

        if ready:
            logging.info(
                f"Adding {len(ready)} of {batch_size} incidents to the GCP "
                "Datastore."
            )
            self._nbd_client.add_incidents(ready)
            logging.info(
                f"Completed adding {len(ready)} of {batch_size} incidents to "
                "the GCP Datastore."
            )

        return len(ready)

    def _process_incident(self, key: str, incident: ScrapedIncident) -> Outcome:
        """Clean and enrich an incident in place, then geocode it."""
        if len(incident) != self.EXPECTED_FIELD_COUNT:
            logging.debug(
                f"This incident has an insufficient number of keys: {incident}"
            )
            return Outcome.MALFORMED

        incident[INCIDENT_KEY_ID] = key
        incident[INCIDENT_KEY_LOCATION] = self._addr_parser.process(
            incident[INCIDENT_KEY_LOCATION]
        )
        address = incident[INCIDENT_KEY_LOCATION].split(" (")[0]

        incident[INCIDENT_KEY_REPORTED] = normalize_reported_timestamp(
            incident[INCIDENT_KEY_REPORTED]
        )
        reported = parse_reported_timestamp(incident[INCIDENT_KEY_REPORTED])
        if reported is None:
            logging.debug(f"This incident has a malformed date: {incident}")
            return Outcome.MALFORMED

        incident[INCIDENT_KEY_TYPE] = self._lemmatize(
            incident[INCIDENT_KEY_TYPE]
        )
        incident[INCIDENT_KEY_COMMENTS] = clean_comments(
            incident[INCIDENT_KEY_COMMENTS]
        )
        self._predict_information_type(incident)

        localized_reported = TIMEZONE_CHICAGO.localize(reported)
        incident[INCIDENT_KEY_REPORTED_DATE] = localized_reported.strftime(
            UCPD_MDY_KEY_DATE_FORMAT
        )
        incident[INCIDENT_KEY_REPORTED] = localized_reported
        incident[INCIDENT_KEY_SEASON] = determine_season(localized_reported)

        geocoded = self._geocoder.get_address_information(address, incident)
        if geocoded and self._has_valid_coordinates(incident):
            return Outcome.READY

        logging.debug(
            "This incident failed to get a valid location with the "
            f"Geocoder: {incident}"
        )
        return Outcome.GEOCODE_FAILED

    def _predict_information_type(self, incident: ScrapedIncident) -> None:
        """Predict a more specific type for 'Information' incidents."""
        if incident[INCIDENT_KEY_TYPE] == INCIDENT_TYPE_INFO:
            self._information_total += 1
            predicted_type = self._classifier.get_predicted_incident_type(
                incident[INCIDENT_KEY_COMMENTS]
            )
            if predicted_type is not None:
                self._information_predicted += 1
                incident[INCIDENT_PREDICTED_TYPE] = predicted_type

        incident.setdefault(INCIDENT_PREDICTED_TYPE, "")

    @staticmethod
    def _has_valid_coordinates(incident: ScrapedIncident) -> bool:
        return (
            INCIDENT_KEY_ADDRESS in incident
            and -90.0 <= incident[INCIDENT_KEY_LATITUDE] <= 90.0
            and -90.0 <= incident[INCIDENT_KEY_LONGITUDE] <= 90.0
        )
