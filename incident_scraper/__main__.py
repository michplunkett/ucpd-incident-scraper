"""Serves as the entry point for the project module."""
import argparse

from click import IntRange

from incident_scraper.external.census import CensusClient
from incident_scraper.external.google_datastore import GoogleNBD
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
        type=IntRange(3, 10),
        default=3,
    )

    subparser.add_parser("seed")

    args = parser.parse_args()

    scraper = UCPDScraper()

    incidents: dict
    if args.command == "days-back":
        if args.days == 3:
            incidents = scraper.scrape_last_three_days()
        elif args.days == 5:
            incidents = scraper.scrape_last_five_days()
        elif args.days == 10:
            incidents = scraper.scrape_last_ten_days()
    elif args.command == "seed":
        incidents = scraper.scrape_from_beginning_2023()

    print(
        f"{len(incidents.keys())} incidents were scraped from the UCPD Incidents' site."
    )
    if len(incidents.keys()):
        census = CensusClient()
        incident_objs = []
        print("Grabbing official address information from the Census Geocoder.")
        for key in incidents.keys():
            i = incidents[key]
            i["UCPD_ID"] = key
            census_resp = census.validate_address(i["Location"].split(" (")[0])
            if census_resp:
                set_validated_location(i, census_resp)
                i["ReportedDate"] = date_str_to_date_format(i["Reported"])
                i["Reported"] = date_str_to_iso_format(i["Reported"])
                incident_objs.append(i)
        print("Finished official address information from Census.")
        print(
            f"{len(incident_objs)} incidents were recovered from the Census Geocoder."
        )
        if len(incident_objs):
            print(
                f"Adding {len(incident_objs)} incidents are being added to the GCP "
                f"Datastore."
            )
            GoogleNBD().add_incidents(incident_objs)
            print(
                f"Finished adding {len(incident_objs)} incidents to the GCP Datastore."
            )


if __name__ == "__main__":
    main()
