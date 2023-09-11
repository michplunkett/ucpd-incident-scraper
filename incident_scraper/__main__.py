"""Serves as the entry point for the project module."""
import argparse
import logging
import sys
from datetime import datetime

import google.cloud.logging as gcp_logging
from click import IntRange

from incident_scraper.external.census import CensusClient
from incident_scraper.external.google_nbd import GoogleNBD
from incident_scraper.models.incident import set_validated_location
from incident_scraper.scraper.ucpd_scraper import UCPDScraper
from incident_scraper.utils.constants import (
    TIMEZONE_CHICAGO,
    UCPD_DATE_FORMAT,
    UCPD_MDY_KEY_DATE_FORMAT,
)


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
    subparser.add_parser("update")

    args = parser.parse_args()

    # General setup
    nbd_client = GoogleNBD()
    scraper = UCPDScraper()
    logging_client = gcp_logging.Client()
    logging_client.setup_logging(log_level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    incidents: dict
    if args.command == "days-back":
        incidents = scraper.scrape_last_days(args.days)
    elif args.command == "seed":
        incidents = scraper.scrape_from_beginning_2023()
    elif args.command == "update":
        day_diff = (datetime.now().date() - nbd_client.get_latest_date()).days
        if day_diff > 0:
            incidents = scraper.scrape_last_days(day_diff - 1)
        else:
            logging.info("Saved incidents are up-to-date.")
            return 0

    total_incidents = len(incidents.keys())
    logging.info(
        f"{total_incidents} total incidents were scraped from the UCPD Incidents' site."
    )
    if total_incidents:
        census = CensusClient()
        # Split list of incidents into groups of 30 and submit them
        n = 30
        total_added_incidents = 0
        list_of_key_lists = [
            list(incidents.keys())[i * n : (i + 1) * n]
            for i in range((total_incidents + n - 1) // n)
        ]
        for key_list in list_of_key_lists:
            incident_objs = []
            geocode_error_incidents = []
            void_incidents = []
            inter_incidents = len(key_list)
            for key in key_list:
                i = incidents[key]

                if not [k for k in i.keys() if i[k] != "Void"]:
                    void_incidents.append(i)
                    continue

                i["UCPD_ID"] = key
                census_resp = census.validate_address(
                    i["Location"].split(" (")[0]
                )
                if census_resp:
                    set_validated_location(i, census_resp)
                    i["Reported"] = i["Reported"].replace(";", ":")
                    i["ReportedDate"] = TIMEZONE_CHICAGO.localize(
                        datetime.strptime(i["Reported"], UCPD_DATE_FORMAT)
                    ).strftime(UCPD_MDY_KEY_DATE_FORMAT)
                    i["Reported"] = TIMEZONE_CHICAGO.localize(
                        datetime.strptime(i["Reported"], UCPD_DATE_FORMAT)
                    )
                    incident_objs.append(i)
                else:
                    geocode_error_incidents.append(i)
                    logging.error(
                        "This incident failed to get a location with the Census "
                        f"Geocoder: {i}"
                    )
            added_incidents = len(incident_objs)
            logging.info(
                f"{len(void_incidents)} of {inter_incidents} contained voided "
                f"information."
            )
            logging.info(
                f"{len(geocode_error_incidents)} of {inter_incidents} could not be "
                f"processed by the Census Geocoder."
            )
            logging.info(
                f"{added_incidents} of {inter_incidents} incidents were successfully "
                f"processed."
            )
            if len(incident_objs):
                logging.info(
                    f"Adding {added_incidents} of {inter_incidents} incidents to the "
                    "GCP Datastore."
                )
                nbd_client.add_incidents(incident_objs)
                logging.info(
                    f"Completed adding {added_incidents} of {inter_incidents} "
                    "incidents to the GCP Datastore."
                )
            total_added_incidents += added_incidents

        logging.info(
            f"{total_incidents - total_added_incidents} of {total_incidents} incidents "
            "were NOT added to the GCP Datastore."
        )


if __name__ == "__main__":
    main()
