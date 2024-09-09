"""Serves as the entry point for the project module."""

import argparse
import logging
import os.path
import re
from datetime import datetime
from typing import Any

from click import IntRange

from incident_scraper.external.geocoder import Geocoder
from incident_scraper.external.google_logger import init_logger
from incident_scraper.external.google_nbd import GoogleNBD
from incident_scraper.external.lemmatizer import Lemmatizer
from incident_scraper.external.maroon_google_drive import MaroonGoogleDrive
from incident_scraper.models.address_parser import AddressParser
from incident_scraper.models.classifier import Classifier
from incident_scraper.models.incident import Incident
from incident_scraper.scraper.ucpd_scraper import UCPDScraper
from incident_scraper.utils.constants import (
    FILE_NAME_INCIDENT_DUMP,
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
    SystemFlags,
)
from incident_scraper.utils.functions import (
    determine_season,
    parse_scraped_incident_timestamp,
)


init_logger()


# TODO: Chop this up into a service or some other organized structure
def main():  # noqa: C901
    """Run the UCPD Incident Scraper."""
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="command")

    days_back = subparser.add_parser(SystemFlags.DAYS_BACK)
    days_back.add_argument(
        "days",
        # The range is locked between 3 and 30.
        type=IntRange(3, 90),
        default=3,
    )

    subparser.add_parser(SystemFlags.BUILD_MODEL)
    subparser.add_parser(SystemFlags.CATEGORIZE)
    subparser.add_parser(SystemFlags.DOWNLOAD)
    subparser.add_parser(SystemFlags.LEMMATIZE_CATEGORIES)
    subparser.add_parser(SystemFlags.SEED)
    subparser.add_parser(SystemFlags.UPDATE)

    args = parser.parse_args()

    # General setup
    nbd_client = GoogleNBD()
    scraper = UCPDScraper()

    incidents = {}
    match args.command:
        case SystemFlags.BUILD_MODEL:
            Classifier(build_model=True).train_and_save()
        case SystemFlags.CATEGORIZE:
            categorize_information(nbd_client)
        case SystemFlags.DAYS_BACK:
            incidents = scraper.scrape_last_days(args.days)
        case SystemFlags.DOWNLOAD:
            nbd_client.download_all()
        case SystemFlags.LEMMATIZE_CATEGORIES:
            lemmatize_categories(nbd_client)
        case SystemFlags.SEED:
            incidents = scraper.scrape_from_beginning_2011()
        case SystemFlags.UPDATE:
            day_diff = (
                datetime.now().date() - nbd_client.get_latest_date()
            ).days
            if day_diff > 0:
                incidents = scraper.scrape_last_days(day_diff - 1)
            else:
                logging.info("Saved incidents are up-to-date.")

    if len(incidents.keys()):
        parse_and_save_records(incidents, nbd_client)


def categorize_information(nbd_client: GoogleNBD) -> None:
    prediction_model = Classifier()
    incidents = nbd_client.get_all_information_incidents()

    # Incident counters
    predicted_labels = 0
    for i in incidents:
        pred_type = prediction_model.get_predicted_incident_type(i.comments)
        if pred_type is not None:
            predicted_labels += 1
            i.predicted_incident = pred_type

    logging.info(
        f"{predicted_labels} of {len(incidents)} 'Information' incidents "
        "were categorized."
    )

    nbd_client.update_list_of_incidents(incidents)


def download_and_upload_records() -> None:
    logging.info("Beginning incident download and Google Drive export.")
    GoogleNBD().download_all()
    if os.path.isfile(FILE_NAME_INCIDENT_DUMP):
        MaroonGoogleDrive().upload_file_to_maroon_tech_folder(
            FILE_NAME_INCIDENT_DUMP
        )
    logging.info("Finished incident download and Google Drive export.")


def lemmatize_categories(nbd_client: GoogleNBD) -> None:
    incidents = nbd_client.get_all_incidents()
    logging.info(f"{len(incidents)} incidents fetched.")

    lemmatized_incidents: [Incident] = []

    for i in incidents:
        lemma_i_type = Lemmatizer.process(i.incident)
        if i.incident != lemma_i_type:
            i.incident = lemma_i_type
            lemmatized_incidents.append(i)

    logging.info(
        f"{len(lemmatized_incidents)} of {len(incidents)} "
        "were incidents lemmatized."
    )

    nbd_client.update_list_of_incidents(lemmatized_incidents)

    logging.info(f"{len(lemmatized_incidents)} types were updated.")


def parse_and_save_records(
    incidents: {str: Any}, nbd_client: GoogleNBD
) -> None:
    """Take incidents and save them to the GCP Datastore."""
    logging.info(
        f"{len(incidents.keys())} total incidents were scraped from the UCPD "
        "Incidents' site."
    )

    # Instantiate clients
    addr_parser = AddressParser()
    geocoder = Geocoder()
    prediction_model = Classifier()
    total_incidents = len(incidents.keys())

    # Split list of incidents into groups of 100 and submit them
    n = 100
    total_added_incidents = 0
    list_of_key_lists = [
        list(incidents.keys())[i * n : (i + 1) * n]
        for i in range((total_incidents + n - 1) // n)
    ]

    # Incident Key Tracking
    num_information_incidents = 0
    information_incidents_predicted = 0

    for key_list in list_of_key_lists:
        incident_objs = []
        geocode_error_incidents = []
        void_malformed_incidents = []
        inter_incidents = len(key_list)
        for key in key_list:
            i = incidents[key]

            if len(i.keys()) != 6:
                void_malformed_incidents.append(i)
                logging.debug(
                    f"This incident has an insufficient number of keys: {i}"
                )
                continue

            i[INCIDENT_KEY_ID] = key

            i[INCIDENT_KEY_LOCATION] = addr_parser.process(
                i[INCIDENT_KEY_LOCATION]
            )

            address = (
                i[INCIDENT_KEY_LOCATION].split(" (")[0]
                if "(" in i[INCIDENT_KEY_LOCATION]
                else i[INCIDENT_KEY_LOCATION]
            )

            i[INCIDENT_KEY_REPORTED] = i[INCIDENT_KEY_REPORTED].replace(
                ";", ":"
            )

            formatted_reported_value = parse_scraped_incident_timestamp(i)

            if not formatted_reported_value:
                void_malformed_incidents.append(i)
                logging.debug(f"This incident has a malformed date: {i}")
                continue

            i[INCIDENT_KEY_TYPE] = Lemmatizer.process(i[INCIDENT_KEY_TYPE])

            i[INCIDENT_KEY_COMMENTS] = (
                i[INCIDENT_KEY_COMMENTS].replace("\n", " ")
            ).strip()

            i[INCIDENT_KEY_COMMENTS] = re.sub(
                r"\s{2,}", " ", i[INCIDENT_KEY_COMMENTS]
            )

            if i[INCIDENT_KEY_TYPE] == INCIDENT_TYPE_INFO:
                num_information_incidents += 1
                pred_type = prediction_model.get_predicted_incident_type(
                    i[INCIDENT_KEY_COMMENTS]
                )
                if pred_type is not None:
                    information_incidents_predicted += 1
                    i[INCIDENT_PREDICTED_TYPE] = pred_type

            if INCIDENT_PREDICTED_TYPE not in i:
                i[INCIDENT_PREDICTED_TYPE] = ""

            i[INCIDENT_KEY_REPORTED_DATE] = TIMEZONE_CHICAGO.localize(
                formatted_reported_value
            ).strftime(UCPD_MDY_KEY_DATE_FORMAT)
            i[INCIDENT_KEY_REPORTED] = TIMEZONE_CHICAGO.localize(
                formatted_reported_value
            )

            i[INCIDENT_KEY_SEASON] = determine_season(i[INCIDENT_KEY_REPORTED])

            if (
                geocoder.get_address_information(address, i)
                and INCIDENT_KEY_ADDRESS in i
                and -90.0 <= i[INCIDENT_KEY_LATITUDE] <= 90.0
                and -90.0 <= i[INCIDENT_KEY_LONGITUDE] <= 90.0
            ):
                incident_objs.append(i)
                continue
            else:
                geocode_error_incidents.append(i)
                logging.debug(
                    "This incident failed to get a valid location with the "
                    f"Geocoder: {i}"
                )

            geocode_error_incidents.append(i)
            logging.debug(
                "This incident failed to get a location with the GoogleMaps' "
                f"Geocoder: {i}"
            )
        added_incidents = len(incident_objs)
        logging.info(
            f"{len(void_malformed_incidents)} of {inter_incidents} contained "
            "malformed or voided information."
        )
        logging.info(
            f"{len(geocode_error_incidents)} of {inter_incidents} could not be "
            f"processed by the Geocoder."
        )
        logging.info(
            f"{added_incidents} of {inter_incidents} incidents were "
            "successfully processed."
        )
        if len(incident_objs):
            logging.info(
                f"Adding {added_incidents} of {inter_incidents} incidents to "
                "the GCP Datastore."
            )
            nbd_client.add_incidents(incident_objs)
            logging.info(
                f"Completed adding {added_incidents} of {inter_incidents} "
                "incidents to the GCP Datastore."
            )
        total_added_incidents += added_incidents

    logging.info(
        f"{information_incidents_predicted} of {num_information_incidents} "
        "'Information' incidents predicted into other categories."
    )
    logging.info(
        f"{total_incidents - total_added_incidents} of {total_incidents} "
        "incidents could NOT be added to the GCP Datastore."
    )


def update_records() -> None:
    """Update incident records based on last scraped incident."""
    nbd_client = GoogleNBD()
    scraper = UCPDScraper()
    day_diff = (datetime.now().date() - nbd_client.get_latest_date()).days
    if day_diff > 0:
        incidents = scraper.scrape_last_days(day_diff - 1)
    else:
        logging.info("Saved incidents are up-to-date.")
        return

    total_incidents = len(incidents.keys())

    if total_incidents:
        parse_and_save_records(incidents, nbd_client)
    else:
        logging.info(
            "No incidents were scraped for "
            f"{datetime.now().strftime(UCPD_MDY_KEY_DATE_FORMAT)}."
        )


if __name__ == "__main__":
    main()
