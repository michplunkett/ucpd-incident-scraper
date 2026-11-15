"""Test the scraper's construction of the URLs it requests."""

from datetime import date
from types import SimpleNamespace

import pytest

from incident_scraper.scraper.ucpd_scraper import UCPDScraper

BASE = "https://incidentreports.uchicago.edu/incidentReportArchive.php"


@pytest.mark.parametrize(
    ("first_day", "last_day", "start_epoch", "end_epoch"),
    [
        # Through the start of the 15th, so that the 14th is included.
        (date(2026, 11, 11), date(2026, 11, 14), 1794376800, 1794722400),
        # A single day, as scraped by an update that is a day behind.
        (date(2026, 11, 12), date(2026, 11, 12), 1794463200, 1794549600),
        # The range from the 2023 scraper's seed URL.
        (date(2011, 1, 1), date(2023, 7, 16), 1293861600, 1689570000),
    ],
)
def test_construct_url(first_day, last_day, start_epoch, end_epoch):
    url = UCPDScraper._construct_url(first_day, last_day)

    assert url == f"{BASE}?startDate={start_epoch}&endDate={end_epoch}&offset="


@pytest.mark.parametrize(
    ("status_code", "content"),
    [(200, b""), (200, b" \n "), (403, b""), (503, b"")],
    ids=["empty-200", "blank-200", "empty-403", "empty-503"],
)
def test_empty_page_raises_an_error_naming_the_status_and_url(
    monkeypatch, status_code, content
):
    url = f"{BASE}?startDate=1&endDate=2&offset=0"
    response = SimpleNamespace(status_code=status_code, content=content)
    monkeypatch.setattr(
        "incident_scraper.scraper.ucpd_scraper.requests.get",
        lambda *args, **kwargs: response,
    )

    with pytest.raises(RuntimeError) as error:
        UCPDScraper(request_delay=0)._get_table(url)

    assert f"HTTP {status_code}" in str(error.value)
    assert url in str(error.value)


def test_only_decodable_encodings_are_requested():
    # requests can't decode brotli unless the brotli package is installed.
    encodings = UCPDScraper()._headers["Accept-Encoding"]

    assert "br" not in [e.strip() for e in encodings.split(",")]
