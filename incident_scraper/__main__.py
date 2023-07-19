"""Serves as the entry point for the project module."""
import argparse

from click import IntRange


def main():
    """Run the UCPD Incident Scraper."""
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-db",
        "--days-back",
        help="Number of days back to scrape the UCPD incident site.",
        # The range is
        type=IntRange(3, 10),
        default=False,
        action=argparse.BooleanOptionalAction,
    )
    group.add_argument(
        "-s" "--seed",
        help="Get all UCPD incidents starting from the beginning of the year.",
        type=bool,
        default=False,
        action=argparse.BooleanOptionalAction,
    )

    args = parser.parse_args()

    if args.days_back:
        print(f"Gonna go {args.days_back} days back.")
    elif args.seed:
        print("Gonna get ALL the incidents")


if __name__ == "__main__":
    main()
