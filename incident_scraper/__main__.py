"""Serves as the entry point for the project module."""
import argparse
import logging
import re
from datetime import datetime
from typing import Any

from click import IntRange
from google.cloud.ndb import GeoPt

from incident_scraper.external.google_logger import init_logger
from incident_scraper.external.google_maps import GoogleMaps
from incident_scraper.external.google_nbd import GoogleNBD
from incident_scraper.models.classifier import Classifier
from incident_scraper.models.incident import set_google_maps_validated_location
from incident_scraper.scraper.ucpd_scraper import UCPDScraper
from incident_scraper.utils.constants import (
    INCIDENT_KEY_COMMENTS,
    INCIDENT_KEY_ID,
    INCIDENT_KEY_LATITUDE,
    INCIDENT_KEY_LOCATION,
    INCIDENT_KEY_LONGITUDE,
    INCIDENT_KEY_REPORTED,
    INCIDENT_KEY_REPORTED_DATE,
    INCIDENT_KEY_TYPE,
    INCIDENT_PREDICTED_TYPE,
    INCIDENT_TYPE_INFO,
    TIMEZONE_CHICAGO,
    UCPD_MDY_KEY_DATE_FORMAT,
)
from incident_scraper.utils.functions import parse_scraped_incident_timestamp


COMMAND_BUILD_MODEL = "build-model"
COMMAND_CATEGORIZE = "categorize"
COMMAND_CORRECT_GEOPT = "correct-geopt"
COMMAND_DAYS_BACK = "days-back"
COMMAND_DOWNLOAD = "download"
COMMAND_SEED = "seed"
COMMAND_UPDATE = "update"


# TODO: Chop this up into a service or some other organized structure
def main():
    """Run the UCPD Incident Scraper."""
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="command")

    days_back = subparser.add_parser(COMMAND_DAYS_BACK)
    days_back.add_argument(
        "days",
        # The range is locked between 3 and 30.
        type=IntRange(3, 30),
        default=3,
    )

    subparser.add_parser(COMMAND_BUILD_MODEL)
    subparser.add_parser(COMMAND_CATEGORIZE)
    subparser.add_parser(COMMAND_CORRECT_GEOPT)
    subparser.add_parser(COMMAND_DOWNLOAD)
    subparser.add_parser(COMMAND_SEED)
    subparser.add_parser(COMMAND_UPDATE)

    args = parser.parse_args()

    # General setup
    nbd_client = GoogleNBD()
    scraper = UCPDScraper()
    init_logger()

    incidents = {}
    if args.command == COMMAND_DAYS_BACK:
        incidents = scraper.scrape_last_days(args.days)
    elif args.command == COMMAND_SEED:
        incidents = scraper.scrape_from_beginning_2011()
    elif args.command == COMMAND_UPDATE:
        day_diff = (datetime.now().date() - nbd_client.get_latest_date()).days
        if day_diff > 0:
            incidents = scraper.scrape_last_days(day_diff - 1)
        else:
            logging.info("Saved incidents are up-to-date.")
            return 0
    elif args.command == COMMAND_DOWNLOAD:
        nbd_client.download_all()
        return 0
    elif args.command == COMMAND_BUILD_MODEL:
        Classifier(build_model=True).train_and_save()
        return 0
    elif args.command == COMMAND_CATEGORIZE:
        categorize_information(nbd_client)
        return 0
    elif args.command == COMMAND_CORRECT_GEOPT:
        correct_location_information(nbd_client)
        return 0

    logging.info(
        f"{len(incidents.keys())} total incidents were scraped from the UCPD "
        "Incidents' site."
    )
    if len(incidents.keys()):
        parse_and_save_records(incidents, nbd_client)


def categorize_information(nbd_client: GoogleNBD) -> None:
    prediction_model = Classifier()
    incidents = nbd_client.get_all_information_incidents()

    # Incident counters
    predicted_labels = 0
    for i in incidents:
        logging.info(i.validated_location.latitude)
        logging.info(i.validated_location.longitude)
        pred_type = prediction_model.get_predicted_incident_type(i.comments)
        if pred_type is not None:
            predicted_labels += 1
            i.predicted_incident = pred_type

    logging.info(
        f"{predicted_labels} of {len(incidents)} 'Information' incidents "
        "were categorized."
    )

    nbd_client.update_list_of_incidents(incidents)


def correct_location_information(nbd_client: GoogleNBD) -> None:
    incidents = nbd_client.get_all_incidents()
    logging.info(f"{len(incidents)} incidents fetched.")
    incidents = [i for i in incidents if i.validated_location.latitude < 0.0]

    logging.info(f"{len(incidents)} incidents had incorrect geocoding.")

    for i in incidents:
        # The location SHOULD be latitude, longitude, but they wer enot mapped
        # correctly upon creation.
        incorrect_latitude = i.validated_location.latitude
        incorrect_longitude = i.validated_location.longitude
        if incorrect_latitude < 0:
            i.validated_location = GeoPt(
                incorrect_longitude, incorrect_latitude
            )

    logging.info(f"{len(incidents)} incorrect incident GeoPts were updated.")

    nbd_client.update_list_of_incidents(incidents)


def parse_and_save_records(
    incidents: {str: Any}, nbd_client: GoogleNBD
) -> None:
    """Take incidents and save them to the GCP Datastore."""
    # Instantiate clients
    google_maps = GoogleMaps()
    total_incidents = len(incidents.keys())
    prediction_model = Classifier()

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
                logging.error(
                    f"This incident has an insufficient number of keys: {i}"
                )
                continue

            i[INCIDENT_KEY_ID] = key
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
                logging.error(f"This incident has a malformed date: {i}")
                continue

            i[INCIDENT_KEY_TYPE] = (
                (
                    i[INCIDENT_KEY_TYPE]
                    .replace("Information / |/ Information ", "")
                    .replace("\\", "/")
                    .replace(" (", " / ")
                    .replace("(", "")
                    .replace(")", "")
                    .replace("&", "and")
                    .replace("Inforation", INCIDENT_TYPE_INFO)
                    .replace("Well Being", "Well-Being")
                    .replace("Infformation", INCIDENT_TYPE_INFO)
                    .replace("Hit & Run", "Hit and Run")
                    .replace("Att.", "Attempted")
                    .replace("Agg.", "Aggravated")
                    .replace("(", "/ ")
                    .replace(")", "")
                    .replace("\n", " ")
                    .replace(" - ", " / ")
                )
                .strip()
                .title()
            )

            i[INCIDENT_KEY_TYPE] = (
                i[INCIDENT_KEY_TYPE]
                .replace("Dui", "DUI")
                .replace("Uc", "UC")
                .replace("Uuw", "Unlawful Use of a Weapon")
                .replace("/", " / ")
            )

            i[INCIDENT_KEY_TYPE] = re.sub(r"\s{2,}", " ", i[INCIDENT_KEY_TYPE])

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

            if (
                set_google_maps_validated_location(
                    i, google_maps.get_address(address)
                )
                and -90.0 <= i[INCIDENT_KEY_LATITUDE] <= 90.0
                and -90.0 <= i[INCIDENT_KEY_LONGITUDE] <= 90.0
            ):
                incident_objs.append(i)
                continue
            else:
                geocode_error_incidents.append(i)
                logging.error(
                    "This incident failed to get a valid location with the "
                    f"GoogleMaps' Geocoder: {i}"
                )

            geocode_error_incidents.append(i)
            logging.error(
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
            f"processed by the GoogleMaps' Geocoder."
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
    init_logger()
    nbd_client = GoogleNBD()
    scraper = UCPDScraper()
    day_diff = (datetime.now().date() - nbd_client.get_latest_date()).days
    if day_diff > 0:
        incidents = scraper.scrape_last_days(day_diff - 1)
    else:
        logging.info("Saved incidents are up-to-date.")
        return 0

    total_incidents = len(incidents.keys())

    logging.info(
        f"{total_incidents} total incidents were scraped from the UCPD "
        "Incidents' site."
    )
    if total_incidents:
        parse_and_save_records(incidents, nbd_client)


if __name__ == "__main__":
    main()
