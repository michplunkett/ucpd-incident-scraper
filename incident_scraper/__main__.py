"""Serves as the entry point for the project module."""

import argparse
import logging
from datetime import datetime
from typing import Any

from click import IntRange

from incident_scraper.external.geocoder import Geocoder
from incident_scraper.external.google_logger import init_logger
from incident_scraper.external.google_nbd import GoogleNBD
from incident_scraper.external.lemmatizer import Lemmatizer
from incident_scraper.models.address_parser import AddressParser
from incident_scraper.models.classifier import Classifier
from incident_scraper.models.incident import Incident
from incident_scraper.scraper.ucpd_scraper import UCPDScraper
from incident_scraper.services.incident_processor import IncidentProcessor
from incident_scraper.utils.constants import SystemFlags

init_logger()


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser for the scraper's sub-commands."""
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="command")

    days_back = subparser.add_parser(SystemFlags.DAYS_BACK)
    days_back.add_argument(
        "days",
        # The range is locked between 3 and 90.
        type=IntRange(3, 90),
        default=3,
    )

    for flag in (
        SystemFlags.BUILD_MODEL,
        SystemFlags.CATEGORIZE,
        SystemFlags.DOWNLOAD,
        SystemFlags.LEMMATIZE_CATEGORIES,
        SystemFlags.SEED,
        SystemFlags.UPDATE,
    ):
        subparser.add_parser(flag)

    return parser


def main():
    """Run the UCPD Incident Scraper."""
    args = build_parser().parse_args()

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
            incidents = scrape_since_latest_incident(nbd_client, scraper)

    if incidents:
        IncidentProcessor(
            nbd_client=nbd_client,
            addr_parser=AddressParser(),
            geocoder=Geocoder(),
            classifier=Classifier(),
            lemmatize=Lemmatizer.process,
        ).process_and_save(incidents)


def scrape_since_latest_incident(
    nbd_client: GoogleNBD, scraper: UCPDScraper
) -> dict[str, Any]:
    """Scrape every day since the latest incident that has been saved."""
    now = datetime.now().date()
    day_diff = (now - nbd_client.get_latest_date()).days
    if day_diff > 0:
        return scraper.scrape_last_days(day_diff - 1)

    if now.isoweekday() not in (6, 7):
        # Use the warning log level if day_diff <= 0, and it's a weekday
        logging.warning(
            f"Scraper did not add any new incidents for {now} "
            f"with a day diff of {day_diff}"
        )

    return {}


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


def lemmatize_categories(nbd_client: GoogleNBD) -> None:
    incidents = nbd_client.get_all_incidents()
    logging.info(f"{len(incidents)} incidents fetched.")

    lemmatized_incidents: list[Incident] = []

    for i in incidents:
        lemma_i_type = Lemmatizer.process(i.incident)
        if i.incident != lemma_i_type:
            i.incident = lemma_i_type
            lemmatized_incidents.append(i)

    logging.info(
        f"{len(lemmatized_incidents)} of {len(incidents)} "
        "incidents were lemmatized."
    )

    nbd_client.update_list_of_incidents(lemmatized_incidents)

    logging.info(f"{len(lemmatized_incidents)} types were updated.")


if __name__ == "__main__":
    main()
