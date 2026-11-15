"""Pure helper functions that are shared across the scraper."""

import re
from collections.abc import Iterator, Sequence
from datetime import datetime
from typing import Any

from incident_scraper.utils.constants import UCPD_TIMESTAMP_FORMAT

# Words that stay lower case in a title: articles, coordinating conjunctions,
# and some short prepositions.
# Source: https://www.geeksforgeeks.org/convert-string-to-title-case-in-python/
_TITLE_CASE_LOWER_WORDS = frozenset(
    {
        # Articles
        "a",
        "an",
        "the",
        # Coordinating conjunctions
        "and",
        "but",
        "for",
        "nor",
        "or",
        "so",
        "yet",
        # Prepositions
        "about",
        "after",
        "against",
        "among",
        "around",
        "as",
        "at",
        "before",
        "between",
        "by",
        "during",
        "from",
        "in",
        "into",
        "like",
        "of",
        "on",
        "out",
        "over",
        "through",
        "to",
        "under",
        "via",
        "with",
        "without",
    }
)

_SEASON_BY_MONTH = {
    **dict.fromkeys((3, 4, 5), "Spring"),
    **dict.fromkeys((6, 7, 8), "Summer"),
    **dict.fromkeys((9, 10, 11), "Fall"),
}

_WHITESPACE_RUN = re.compile(r"\s{2,}")

# The UCPD site is inconsistent with the timestamps it publishes, so they are
# repaired in two passes (in order), with the whitespace collapsed in between.
# A space is always put in front of the meridiem here, and any surplus is
# removed by the collapse that follows.
_TIMESTAMP_REPLACEMENTS_BEFORE_COLLAPSE = (
    (";", ":"),
    ("AM", " AM"),
    ("PM", " PM"),
)
_TIMESTAMP_REPLACEMENTS_AFTER_COLLAPSE = (
    ("//", "/"),
    ("!", "1"),
    (" at ", " "),
    (":PM", " PM"),
    (":AM", " AM"),
    (": PM", " PM"),
    (": AM", " AM"),
    (": ", ":"),
)


def custom_title_case(input_string: str) -> str:
    """Title case a string, leaving small words like 'of' or 'and' as is."""
    return " ".join(
        word if word in _TITLE_CASE_LOWER_WORDS else word.title()
        for word in input_string.split(" ")
    )


def collapse_whitespace(text: str) -> str:
    """Replace every run of two or more whitespace characters with a space."""
    return _WHITESPACE_RUN.sub(" ", text)


def clean_comments(comments: str) -> str:
    """Flatten a scraped comment onto a single, tidy line."""
    return collapse_whitespace(comments.replace("\n", " ").strip())


def normalize_reported_timestamp(timestamp: str) -> str:
    """Compensate for the irregularities in scraped 'Reported' timestamps."""
    for old, new in _TIMESTAMP_REPLACEMENTS_BEFORE_COLLAPSE:
        timestamp = timestamp.replace(old, new)

    timestamp = collapse_whitespace(timestamp)

    for old, new in _TIMESTAMP_REPLACEMENTS_AFTER_COLLAPSE:
        timestamp = timestamp.replace(old, new)

    return timestamp


def parse_reported_timestamp(timestamp: str) -> datetime | None:
    """Parse a normalized timestamp, or return None if it doesn't fit."""
    try:
        return datetime.strptime(timestamp, UCPD_TIMESTAMP_FORMAT)
    except ValueError:
        return None


def determine_season(test_date: datetime) -> str:
    """Get the meteorological season (Winter is December through February)."""
    return _SEASON_BY_MONTH.get(test_date.month, "Winter")


def chunked(items: Sequence[Any], size: int) -> Iterator[Sequence[Any]]:
    """Yield consecutive slices of `items` that are at most `size` long."""
    for start in range(0, len(items), size):
        yield items[start : start + size]
