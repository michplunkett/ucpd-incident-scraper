"""Test the pure helper functions."""

from datetime import datetime

import pytest

from incident_scraper.utils.functions import (
    chunked,
    clean_comments,
    collapse_whitespace,
    custom_title_case,
    determine_season,
    normalize_reported_timestamp,
    parse_reported_timestamp,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("thing       stuff", "thing stuff"),
        ("thing      / stuff", "thing / stuff"),
        ("a \t\n b", "a b"),
        ("single space", "single space"),
        ("", ""),
    ],
)
def test_collapse_whitespace(text, expected):
    assert collapse_whitespace(text) == expected


@pytest.mark.parametrize(
    ("comments", "expected"),
    [
        ("stuff\n/ thing", "stuff / thing"),
        ("  padded  ", "padded"),
        ("line one\n\nline two", "line one line two"),
        ("double   spaced\n text", "double spaced text"),
        ("already clean", "already clean"),
    ],
)
def test_clean_comments(comments, expected):
    assert clean_comments(comments) == expected


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        ("01/05/24 03:45 PM", "01/05/24 03:45 PM"),
        ("1/5/24 3:45PM", "1/5/24 3:45 PM"),
        ("1/5/24  3:45 AM", "1/5/24 3:45 AM"),
        ("1//5/24 3:45 PM", "1/5/24 3:45 PM"),
        ("1/5/24 at 3:45 PM", "1/5/24 3:45 PM"),
        ("1/5/24 3:45:PM", "1/5/24 3:45 PM"),
        ("1/5/24 3; 45 PM", "1/5/24 3:45 PM"),
        ("1/!/24 3:45 PM", "1/1/24 3:45 PM"),
        ("6/1/24 11: AM", "6/1/24 11 AM"),
        ("not a date", "not a date"),
    ],
)
def test_normalize_reported_timestamp(timestamp, expected):
    assert normalize_reported_timestamp(timestamp) == expected


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        ("1/5/24 3:45 PM", datetime(2024, 1, 5, 15, 45)),
        ("01/05/24 03:45 PM", datetime(2024, 1, 5, 15, 45)),
        ("1/5/24 3:45 AM", datetime(2024, 1, 5, 3, 45)),
        # Timestamps as the UCPD site publishes them
        ("11/12/26 7:01 AM", datetime(2026, 11, 12, 7, 1)),
        ("11/12/26 10:10 AM", datetime(2026, 11, 12, 10, 10)),
        ("11/11/26 6:38 PM", datetime(2026, 11, 11, 18, 38)),
        ("11/12/26 2:29 PM", datetime(2026, 11, 12, 14, 29)),
        ("11/12/26 4:35 PM", datetime(2026, 11, 12, 16, 35)),
        ("1/5/24 12:05 AM", datetime(2024, 1, 5, 0, 5)),
        ("not a date", None),
        ("1/5/24 25:00", None),
        ("7/4/24 14:05", None),
        ("13/45/24 3:45 PM", None),
        ("", None),
    ],
)
def test_parse_reported_timestamp(timestamp, expected):
    assert parse_reported_timestamp(timestamp) == expected


@pytest.mark.parametrize(
    ("raw_timestamp", "expected"),
    [
        ("1/5/24 3:45PM", datetime(2024, 1, 5, 15, 45)),
        ("1//5/24 at 3:45:PM", datetime(2024, 1, 5, 15, 45)),
        ("1/5/24 3; 45 PM", datetime(2024, 1, 5, 15, 45)),
    ],
)
def test_messy_timestamps_parse_after_normalizing(raw_timestamp, expected):
    normalized = normalize_reported_timestamp(raw_timestamp)

    assert parse_reported_timestamp(normalized) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("theft", "Theft"),
        ("THEFT", "Theft"),
        ("criminal damage", "Criminal Damage"),
        ("theft of property", "Theft of Property"),
        ("assault and battery", "Assault and Battery"),
        ("trespass to property", "Trespass to Property"),
    ],
)
def test_custom_title_case(text, expected):
    assert custom_title_case(text) == expected


@pytest.mark.parametrize(
    ("month", "day", "expected"),
    [
        (1, 1, "Winter"),
        (1, 15, "Winter"),
        (2, 29, "Winter"),
        (3, 1, "Spring"),
        (4, 15, "Spring"),
        (5, 31, "Spring"),
        (6, 1, "Summer"),
        (7, 4, "Summer"),
        (8, 31, "Summer"),
        (9, 1, "Fall"),
        (10, 15, "Fall"),
        (11, 30, "Fall"),
        (12, 1, "Winter"),
        (12, 31, "Winter"),
    ],
)
def test_determine_season(month, day, expected):
    assert determine_season(datetime(2024, month, day)) == expected


@pytest.mark.parametrize(
    ("items", "size", "expected"),
    [
        ([], 3, []),
        ([1, 2, 3], 3, [[1, 2, 3]]),
        ([1, 2, 3], 5, [[1, 2, 3]]),
        ([1, 2, 3, 4, 5], 2, [[1, 2], [3, 4], [5]]),
        (list(range(6)), 3, [[0, 1, 2], [3, 4, 5]]),
    ],
)
def test_chunked(items, size, expected):
    assert [list(chunk) for chunk in chunked(items, size)] == expected
