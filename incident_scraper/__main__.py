"""Serves as the entry point for the project module."""
import argparse

from click import IntRange

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
        if days_back == 3:
            incidents = scraper.scrape_last_three_days()
        elif days_back == 5:
            incidents = scraper.scrape_last_five_days()
        elif days_back == 10:
            incidents = scraper.scrape_last_ten_days()
    elif args.command == "seed":
        incidents = scraper.scrape_from_beginning_2023()

    print(f"We scraped this many incidents: {len(incidents)}")


if __name__ == "__main__":
    main()
