"""Serves as the entry point for the project module."""
import argparse

from click import IntRange


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

    if args.command == "days-back":
        print(f"Gonna go {args.days} days back.")
    elif args.command == "seed":
        print("Gonna get ALL the incidents")


if __name__ == "__main__":
    main()
