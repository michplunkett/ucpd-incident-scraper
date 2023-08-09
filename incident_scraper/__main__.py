"""Serves as the entry point for the project module."""
import argparse
import logging
import sys

import google.cloud.logging as gcp_logging
from click import IntRange

from incident_scraper.external.census import CensusClient
from incident_scraper.external.google_nbd import GoogleNBD
from incident_scraper.models.incident import (
    date_str_to_date_format,
    date_str_to_iso_format,
    set_validated_location,
)
from incident_scraper.scraper.ucpd_scraper import UCPDScraper


def main():
    """Run the UCPD Incident Scraper."""
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="command")

    days_back = subparser.add_parser("days-back")
    days_back.add_argument(
        "days",
        # The range is locked between 3 and 10.
        type=IntRange(3, 20),
        default=3,
    )

    subparser.add_parser("seed")

    args = parser.parse_args()

    # General setup
    scraper = UCPDScraper()
    logging_client = gcp_logging.Client()
    logging_client.setup_logging()
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    incidents: dict
    if args.command == "days-back":
        incidents = scraper.scrape_back_n_days(args.days)
    elif args.command == "seed":
        incidents = scraper.scrape_from_beginning_2023()

    total_incidents = len(incidents.keys())
    logging.info(
        f"{total_incidents} incidents were scraped from the UCPD Incidents' site."
    )
    if total_incidents:
        census = CensusClient()
        # Split list of incidents into groups of 30 and submit them
        n = 30
        added_incidents = 0
        list_of_key_lists = [
            list(incidents.keys())[i * n : (i + 1) * n]
            for i in range((total_incidents + n - 1) // n)
        ]
        for key_list in list_of_key_lists:
            incident_objs = []
            logging.info(
                "Getting address information from the Census Geocoder."
            )
            for key in key_list:
                i = incidents[key]
                i["UCPD_ID"] = key
                census_resp = census.validate_address(
                    i["Location"].split(" (")[0]
                )
                if census_resp:
                    set_validated_location(i, census_resp)
                    i["ReportedDate"] = date_str_to_date_format(i["Reported"])
                    i["Reported"] = date_str_to_iso_format(i["Reported"])
                    incident_objs.append(i)
                else:
                    logging.debug(i)
            added_incidents += len(incident_objs)
            logging.info("Finished getting address information from Census.")
            logging.info(
                f"{added_incidents} of {total_incidents} incidents were recovered from "
                "the Census Geocoder."
            )
            if len(incident_objs):
                logging.info(
                    f"Adding {added_incidents} of {total_incidents} incidents to the "
                    "GCP Datastore."
                )
                GoogleNBD().add_incidents(incident_objs)
                logging.info(
                    f"Finished adding {added_incidents} of {total_incidents} incidents "
                    "to the GCP Datastore."
                )
        logging.info(
            f"Completed adding {added_incidents} of {total_incidents} incidents to the "
            "GCP Datastore."
        )
        logging.info(
            f"{total_incidents - added_incidents} of {total_incidents} incidents were "
            f"not added to the GCP Datastore due to bad Census Geocoder responses."
        )


if __name__ == "__main__":
    main()
